"""Native metadata selection and lazy encoded-audio iteration for both formats."""
import argparse
import io
import json
from pathlib import Path

import soundfile as sf
import torch
import pyarrow.dataset as ds
import vortex as vx

from common import FILENAMES, SCHEMA_VERSION, packages, preflight, sha256_file, write_json

METADATA_COLUMNS = ["row_index", "id", "speaker_id", "text", "duration_s", "word_count"]
AUDIO_COLUMNS = ["row_index", "id", "text", "sample_rate", "num_frames", "audio_bytes"]
SCAN_BATCH_SIZE = 64
CRITERIA = {"duration_s_min": 3, "duration_s_max": 10, "word_count_min": 5, "bounds": "inclusive"}
READER_SETTINGS = {
    "vortex": dict(use_threads=False, segment_cache=False, readahead="not implemented",
                   mmap="no public setting"),
    "parquet": dict(use_threads=False, batch_readahead=0, fragment_readahead=0, mmap=False),
}


def predicate():
    return ((ds.field("duration_s") >= 3) & (ds.field("duration_s") <= 10)
            & (ds.field("word_count") >= 5))


def reference_selection(rows):
    """Plain independent predicate, used outside timed reader paths."""
    return [row for row in rows if row["duration_s"] is not None and row["word_count"] is not None
            and 3 <= row["duration_s"] <= 10 and row["word_count"] >= 5]


def _open_dataset(path, format_name):
    if format_name == "vortex":
        return vx.open(str(path), without_segment_cache=True).to_dataset()
    if format_name == "parquet":
        return ds.dataset(path, format="parquet")
    raise ValueError(f"Unknown format: {format_name}")


def iter_records(format_name, data_dir="data", columns=None, scan_batch_size=SCAN_BATCH_SIZE, filtered=True, chunk_sizes=None):
    """Yield native scan records. Call preflight explicitly before public use.

    At most one native Arrow chunk is converted to Python rows at a time.
    No manifest membership, Python row filtering, or audio decoding is used.
    """
    if format_name not in FILENAMES:
        raise ValueError(f"Unknown format: {format_name}")
    if scan_batch_size <= 0:
        raise ValueError("scan_batch_size must be positive")
    dataset = _open_dataset(Path(data_dir) / FILENAMES[format_name], format_name)
    kwargs = dict(columns=columns if columns is not None else AUDIO_COLUMNS,
                  filter=predicate() if filtered else None,
                  batch_size=scan_batch_size, use_threads=False)
    if format_name == "parquet":
        kwargs.update(batch_readahead=0, fragment_readahead=0)
    scanner = dataset.scanner(**kwargs)
    batches = iter(scanner.to_batches())
    try:
        for batch in batches:
            if chunk_sizes is not None:
                chunk_sizes.append(batch.num_rows)
            yield from batch.to_pylist()
    finally:
        close = getattr(batches, "close", None)
        if close is not None:
            close()
        # VortexFile/Dataset expose no close() method in the pinned version.
        # Release scanner/iterator references on exhaustion and generator.close().
        batches = scanner = dataset = None


def select_metadata(format_name, data_dir="data", scan_batch_size=SCAN_BATCH_SIZE):
    return list(iter_records(format_name, data_dir, METADATA_COLUMNS, scan_batch_size))


def iter_audio_records(format_name, data_dir="data", scan_batch_size=SCAN_BATCH_SIZE, chunk_sizes=None):
    return iter_records(format_name, data_dir, AUDIO_COLUMNS, scan_batch_size, chunk_sizes=chunk_sizes)


def verify_membership(data_dir="data"):
    manifest = preflight(data_dir)
    source = list(iter_records("parquet", data_dir, METADATA_COLUMNS, filtered=False))
    if [row["id"] for row in source] != manifest["ordered_ids"]:
        raise ValueError("Source metadata does not match preparation membership")
    expected = reference_selection(source)
    if not expected:
        raise ValueError("Default real-data selection is empty")
    for format_name in FILENAMES:
        if select_metadata(format_name, data_dir) != expected:
            raise ValueError(f"{format_name} selection differs from reference")
        records = iter_audio_records(format_name, data_dir)
        try:
            for row in expected:
                actual = next(records, None)
                if actual is None:
                    raise ValueError("Missing selected audio record")
                if (actual["id"], actual["row_index"]) != (row["id"], row["row_index"]):
                    raise ValueError("Selected audio order differs from metadata")
                from common import sha256_bytes
                if sha256_bytes(actual["audio_bytes"]) != manifest["audio_sha256"][row["row_index"]]:
                    raise ValueError(f"Clip {actual['id']}: selected audio differs from preparation")
            if next(records, None) is not None:
                raise ValueError("Extra selected audio record")
        finally:
            records.close()
    return manifest, expected


def save_selection(data_dir="data"):
    manifest, selected = verify_membership(data_dir)
    value = dict(schema_version=SCHEMA_VERSION, criteria=CRITERIA, source=manifest["source"],
                 preparation_sha256=sha256_file(Path(data_dir) / "preparation.json"),
                 file_hashes={fmt: info["sha256"] for fmt, info in manifest["files"].items()},
                 selected_count=len(selected), ordered_ids=[row["id"] for row in selected],
                 row_indices=[row["row_index"] for row in selected], packages=packages())
    write_json(Path(data_dir) / "selection.json", value)
    return value


def validate_selection(data_dir="data"):
    manifest = preflight(data_dir)
    path = Path(data_dir) / "selection.json"
    if not path.is_file():
        raise ValueError("Missing selection.json; run loaders.py first")
    selection = json.loads(path.read_text())
    if (selection.get("schema_version") != SCHEMA_VERSION or selection.get("criteria") != CRITERIA
            or selection.get("source") != manifest["source"]
            or selection.get("preparation_sha256") != sha256_file(Path(data_dir) / "preparation.json")
            or selection.get("file_hashes") != {fmt: item["sha256"] for fmt, item in manifest["files"].items()}):
        raise ValueError("Stale selection manifest")
    indices, ids = selection["row_indices"], selection["ordered_ids"]
    if (not indices or indices != sorted(set(indices)) or len(indices) != selection["selected_count"]
            or len(ids) != len(indices) or any(not 0 <= index < manifest["row_count"] for index in indices)
            or ids != [manifest["ordered_ids"][index] for index in indices]):
        raise ValueError("Invalid selection membership")
    return selection



def decode_record(record):
    """Return mono float32 samples; never resample or normalize source audio."""
    clip_id = record.get("id", "<missing>")
    try:
        samples, rate = sf.read(io.BytesIO(record["audio_bytes"]), dtype="float32")
        if samples.ndim != 1 or not len(samples):
            raise ValueError("expected nonempty mono samples")
        if rate != 16000 or record["sample_rate"] != rate:
            raise ValueError("expected consistent 16 kHz sample rate")
        if record["num_frames"] != len(samples):
            raise ValueError("decoded frame count differs from metadata")
        return samples
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        raise ValueError(f"Clip {clip_id}: {error}") from error


def _collate(decoded):
    lengths = torch.tensor([len(samples) for _, samples in decoded], dtype=torch.int64)
    waveforms = torch.zeros((len(decoded), int(lengths.max())), dtype=torch.float32)
    for index, (_, samples) in enumerate(decoded):
        waveforms[index, :len(samples)] = torch.from_numpy(samples)
    return dict(waveforms=waveforms, lengths=lengths,
                transcripts=[record["text"] for record, _ in decoded],
                ids=[record["id"] for record, _ in decoded], sample_rate=16000)


def batch_records(records, batch_size=16):
    """Collate across scanner chunks; retain only the current batch of samples."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    iterator = iter(records)
    current = []
    try:
        for record in iterator:
            current.append((record, decode_record(record)))
            if len(current) == batch_size:
                yield _collate(current)
                current = []
        if current:
            yield _collate(current)
    finally:
        close = getattr(iterator, "close", None)
        if close is not None:
            close()
        current.clear()
        iterator = None


def iter_batches(format_name, data_dir="data", batch_size=16, scan_batch_size=SCAN_BATCH_SIZE, chunk_sizes=None):
    return batch_records(iter_audio_records(format_name, data_dir, scan_batch_size, chunk_sizes), batch_size)


def verify_batches(data_dir="data"):
    """Full untimed correctness gate with bounded waveform retention."""
    _, expected = verify_membership(data_dir)
    left = iter_batches("vortex", data_dir)
    right = iter_batches("parquet", data_dir)
    ids, count = [], 0
    try:
        while True:
            a, b = next(left, None), next(right, None)
            if a is None or b is None:
                if a is not None or b is not None:
                    raise ValueError("Different batch counts")
                break
            for key in ("ids", "transcripts", "sample_rate"):
                if a[key] != b[key]:
                    raise ValueError(f"Different batch {key}")
            if not torch.equal(a["lengths"], b["lengths"]) or not torch.equal(a["waveforms"], b["waveforms"]):
                raise ValueError("Different waveform values or lengths")
            for batch in (a, b):
                if batch["waveforms"].dtype != torch.float32 or batch["lengths"].dtype != torch.int64:
                    raise ValueError("Invalid tensor dtype")
                if batch["waveforms"].shape != (len(batch["ids"]), int(batch["lengths"].max())):
                    raise ValueError("Invalid padded tensor shape")
                for index, length in enumerate(batch["lengths"].tolist()):
                    if torch.count_nonzero(batch["waveforms"][index, length:]):
                        raise ValueError("Nonzero padding")
            ids.extend(a["ids"])
            count += 1
    finally:
        left.close()
        right.close()
    if ids != [row["id"] for row in expected] or count != (len(expected) + 15) // 16:
        raise ValueError("Batch membership or count differs from reference")
    return dict(selected_count=len(ids), batch_count=count)

def main():
    parser = argparse.ArgumentParser(description="Verify both selections and save a provenance-only manifest")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--verify-batches", action="store_true", help="Verify full PyTorch batch equivalence")
    args = parser.parse_args()
    try:
        result = save_selection(args.data_dir)
        if args.verify_batches:
            print(f"Batch equivalence verified: {verify_batches(args.data_dir)}")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Selection failed: {error}\n")
    print(f"Selected {result['selected_count']} clips; wrote {args.data_dir / 'selection.json'}")


if __name__ == "__main__":
    main()
