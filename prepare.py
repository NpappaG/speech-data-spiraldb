"""Stream a pinned LibriSpeech prefix and publish equivalent local files."""
import argparse
import io
import re
import tempfile
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import soundfile as sf
import vortex as vx

from common import FILENAMES, SCHEMA, SCHEMA_VERSION, packages, sha256_bytes, sha256_file, write_json

SOURCE = "openslr/librispeech_asr"
CONFIG = "clean"
SPLIT = "train.100"
# Immutable source commit verified during M02.
DEFAULT_REVISION = "71cacbfb7e2354c4226d01e70d77d5fca3d04ba1"


def canonical_record(record, row_index):
    clip_id = record.get("id")
    try:
        if not isinstance(clip_id, str) or not clip_id:
            raise ValueError("missing or invalid ID")
        if not isinstance(record["text"], str) or record["speaker_id"] is None:
            raise ValueError("invalid transcript or speaker ID")
        audio = record["audio"]
        payload = audio.get("bytes")
        if payload is None:
            path = audio.get("path")
            if not path or not Path(path).is_file():
                raise ValueError("encoded bytes absent and audio path is not accessible")
            payload = Path(path).read_bytes()
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("empty or invalid encoded audio")
        info = sf.info(io.BytesIO(payload))
        if info.channels != 1 or info.samplerate != 16000 or info.frames <= 0:
            raise ValueError("expected nonempty mono 16 kHz audio")
        return dict(row_index=row_index, id=clip_id, speaker_id=int(record["speaker_id"]),
                    text=record["text"], duration_s=info.frames / info.samplerate,
                    word_count=len(record["text"].split()), sample_rate=info.samplerate,
                    num_frames=info.frames, audio_bytes=payload)
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        raise ValueError(f"Clip {clip_id}: {error}") from error


def build_table(records, limit):
    if limit <= 0:
        raise ValueError("limit must be positive")
    rows, seen = [], set()
    iterator = iter(records)
    try:
        for index in range(limit):
            try:
                row = canonical_record(next(iterator), index)
            except StopIteration as error:
                raise ValueError(f"Source exhausted at {index}; requested {limit} rows") from error
            if row["id"] in seen:
                raise ValueError(f"Clip {row['id']}: duplicate ID")
            seen.add(row["id"])
            rows.append(row)
    finally:
        close = getattr(iterator, "close", None)
        if close is not None:
            close()
    return pa.Table.from_pylist(rows, schema=SCHEMA)


def read_table(path, format_name):
    dataset = (vx.open(str(path)).to_dataset() if format_name == "vortex"
               else ds.dataset(path, format="parquet"))
    return dataset.scanner(use_threads=False).to_table().cast(SCHEMA)


def publish(table, out_dir, source, elapsed_start, overwrite=False):
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    targets = [directory / name for name in (*FILENAMES.values(), "preparation.json", "selection.json")]
    if not overwrite and any(path.exists() for path in targets):
        raise ValueError("Output artifacts exist; use --overwrite or a fresh --output-dir")
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=directory) as staging_dir:
        staging = Path(staging_dir)
        vx.io.write(vx.array(table), str(staging / FILENAMES["vortex"]))
        pq.write_table(table, staging / FILENAMES["parquet"], compression="zstd")
        files = {}
        for format_name, filename in FILENAMES.items():
            path = staging / filename
            if not read_table(path, format_name).equals(table):
                raise ValueError(f"{format_name} output differs from canonical source")
            files[format_name] = dict(name=filename, size_bytes=path.stat().st_size,
                                     sha256=sha256_file(path))
        manifest = dict(schema_version=SCHEMA_VERSION, source=source, row_count=table.num_rows,
                        schema=str(SCHEMA), ordered_ids=table["id"].to_pylist(),
                        audio_sha256=[sha256_bytes(value) for value in table["audio_bytes"].to_pylist()],
                        packages=packages(), files=files,
                        settings=dict(vortex_writer="default", parquet_compression="zstd",
                                      parquet_row_group_size="default", word_count="len(text.split())",
                                      duration_s="num_frames / sample_rate", audio_decode=False,
                                      source_pre_buffer=False, source_use_threads=False, source_scan_batch_size=64,
                                      source_reader="ParquetFile over declared HF shards", source_iterator_closed=True),
                        preparation_seconds=time.perf_counter() - elapsed_start)
        # Invalidate old provenance before replacing any file. Publish manifest last;
        # interrupted publication cannot pass preflight as a complete generation.
        for name in ("preparation.json", "selection.json"):
            (directory / name).unlink(missing_ok=True)
        for filename in FILENAMES.values():
            (staging / filename).replace(directory / filename)
        write_json(directory / "preparation.json", manifest)
    return manifest



def stream_source_files(files, filesystem):
    """Read declared source shards synchronously, preserving their order.

    Dataset async scanners over Python remote file objects can hang at shutdown
    after early termination. The ParquetFile API avoids that background scan;
    acquisition is untimed, so reliability matters more than read parallelism.
    """
    for filename in files:
        with filesystem.open(filename, "rb") as handle:
            parquet = pq.ParquetFile(handle, pre_buffer=False)
            try:
                for batch in parquet.iter_batches(batch_size=64, use_threads=False):
                    yield from batch.to_pylist()
            finally:
                parquet.close()

def prepare(limit=1000, revision=None, output_dir="data", overwrite=False):
    if limit <= 0:
        raise ValueError("limit must be positive")
    directory = Path(output_dir)
    if not overwrite and any((directory / name).exists() for name in (*FILENAMES.values(), "preparation.json")):
        raise ValueError("Output artifacts exist; use --overwrite or a fresh --output-dir")
    from datasets import load_dataset_builder
    from huggingface_hub import HfApi, HfFileSystem
    start = time.perf_counter()
    requested = revision or DEFAULT_REVISION
    resolved = HfApi(token=False).dataset_info(SOURCE, revision=requested).sha
    if not re.fullmatch(r"[0-9a-f]{40}", resolved):
        raise ValueError("Source did not resolve to an immutable commit")
    print(f"Streaming {limit} rows at {resolved}", flush=True)
    builder = load_dataset_builder(SOURCE, CONFIG, revision=resolved,
                                   cache_dir=str(directory / "hf-cache"), token=False)
    files = list(builder.config.data_files[SPLIT])
    if not files or any(f"@{resolved}/" not in filename or not filename.endswith(".parquet") for filename in files):
        raise ValueError("Expected declared Parquet shards pinned to the resolved revision")
    filesystem = HfFileSystem(token=False, skip_instance_cache=True)
    source = stream_source_files(files, filesystem)
    table = build_table(source, limit)
    return publish(table, directory, dict(dataset=SOURCE, config=CONFIG, split=SPLIT,
                                         revision=resolved, limit=limit, source_files=files), start, overwrite)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        result = prepare(args.limit, args.revision, args.output_dir, args.overwrite)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Preparation failed: {error}\n")
    print(f"Published {result['row_count']} rows in {args.output_dir}; both formats verified")


if __name__ == "__main__":
    main()
