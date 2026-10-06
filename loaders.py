"""Native metadata selection and lazy encoded-audio iteration for both formats."""
import argparse
import json
from pathlib import Path

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


def iter_records(format_name, data_dir="data", columns=None, scan_batch_size=SCAN_BATCH_SIZE, filtered=True):
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


def iter_audio_records(format_name, data_dir="data", scan_batch_size=SCAN_BATCH_SIZE):
    return iter_records(format_name, data_dir, AUDIO_COLUMNS, scan_batch_size)


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


def main():
    parser = argparse.ArgumentParser(description="Verify both selections and save a provenance-only manifest")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    try:
        result = save_selection(args.data_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Selection failed: {error}\n")
    print(f"Selected {result['selected_count']} clips; wrote {args.data_dir / 'selection.json'}")


if __name__ == "__main__":
    main()
