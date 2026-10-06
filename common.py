"""Shared artifact contracts; expensive validation is an explicit preflight."""
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import pyarrow as pa

SCHEMA_VERSION = 1
SCHEMA = pa.schema([
    pa.field("row_index", pa.int64(), nullable=False),
    pa.field("id", pa.string(), nullable=False),
    pa.field("speaker_id", pa.int64(), nullable=False),
    pa.field("text", pa.string(), nullable=False),
    pa.field("duration_s", pa.float64(), nullable=False),
    pa.field("word_count", pa.int64(), nullable=False),
    pa.field("sample_rate", pa.int32(), nullable=False),
    pa.field("num_frames", pa.int64(), nullable=False),
    pa.field("audio_bytes", pa.binary(), nullable=False),
])
FILENAMES = {"vortex": "clips.vortex", "parquet": "clips.parquet"}


def packages():
    return {name: version(name) for name in (
        "vortex-data", "pyarrow", "torch", "datasets", "soundfile", "numpy", "pytest"
    )}


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def preflight(data_dir):
    """Check manifest and hashes once before use, outside benchmark timers."""
    directory = Path(data_dir)
    path = directory / "preparation.json"
    if not path.exists():
        raise ValueError(f"Missing {path}; run prepare.py first")
    manifest = json.loads(path.read_text())
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported preparation schema version")
    count = manifest.get("row_count")
    if not isinstance(count, int) or count <= 0:
        raise ValueError("Invalid preparation row count")
    ids = manifest.get("ordered_ids", [])
    hashes = manifest.get("audio_sha256", [])
    if len(ids) != count or len(set(ids)) != count or len(hashes) != count:
        raise ValueError("Invalid preparation membership")
    for format_name, filename in FILENAMES.items():
        details = manifest["files"][format_name]
        path = directory / filename
        if details["name"] != filename or not path.is_file():
            raise ValueError(f"Missing or unexpected {format_name} artifact")
        if path.stat().st_size != details["size_bytes"] or sha256_file(path) != details["sha256"]:
            raise ValueError(f"Stale or mismatched {format_name} artifact; prepare again")
    return manifest
