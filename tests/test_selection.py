import time

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import vortex as vx

import loaders
from common import preflight, write_json
from prepare import build_table, publish


@pytest.mark.parametrize("fmt", ["vortex", "parquet"])
@pytest.mark.parametrize("case,expected", [
    ("boundaries", [1, 2, 5]), ("empty", []), ("none", []),
    ("all", list(range(6))), ("nulls", [2, 5]),
])
def test_each_reader_against_independent_oracle(fmt, case, expected, canonical_table, tmp_path):
    rows = canonical_table.to_pylist()
    if case == "empty":
        rows = []
    elif case == "none":
        for row in rows:
            row["duration_s"] = 11
    elif case == "all":
        for row in rows:
            row["duration_s"], row["word_count"] = 5, 5
    elif case == "nulls":
        rows[1]["duration_s"] = None
        rows[4]["word_count"] = None
    schema = pa.schema([field.with_nullable(True) for field in canonical_table.schema])
    table = pa.Table.from_pylist(rows, schema=schema)
    path = tmp_path / f"clips.{fmt}"
    if fmt == "vortex":
        vx.io.write(vx.array(table), str(path))
    else:
        pq.write_table(table, path, compression="zstd")
    assert [row["row_index"] for row in loaders.reference_selection(rows)] == expected
    metadata = loaders.select_metadata(fmt, tmp_path, scan_batch_size=2)
    assert [row["row_index"] for row in metadata] == expected
    assert all(set(row) == set(loaders.METADATA_COLUMNS) for row in metadata)
    audio = list(loaders.iter_audio_records(fmt, tmp_path, scan_batch_size=2))
    assert [row["row_index"] for row in audio] == expected
    assert [row["audio_bytes"] for row in audio] == [canonical_table["audio_bytes"][i].as_py() for i in expected]


def test_scanner_arguments_laziness_and_cleanup(monkeypatch):
    calls, consumed, closed = [], [], []
    class Scanner:
        def to_batches(self):
            try:
                for i in range(3):
                    consumed.append(i)
                    yield pa.RecordBatch.from_pylist([{"row_index": i, "id": str(i)}])
            finally:
                closed.append(True)
    class Dataset:
        def scanner(self, **kwargs):
            calls.append(kwargs)
            return Scanner()
    monkeypatch.setattr(loaders, "_open_dataset", lambda *args: Dataset())
    stream = loaders.iter_records("vortex", columns=["row_index", "id"], scan_batch_size=1)
    assert calls == []
    assert next(stream)["id"] == "0"
    assert consumed == [0]
    assert calls[0]["columns"] == ["row_index", "id"]
    assert calls[0]["filter"] is not None and calls[0]["use_threads"] is False
    assert calls[0]["batch_size"] == 1
    stream.close()
    assert closed == [True]


def test_stale_selection_manifest(known_audio, tmp_path):
    payload, _ = known_audio
    records = [{"id": "a", "speaker_id": 7, "text": "one two three four five", "audio": {"bytes": payload}}]
    table = build_table(records, 1)
    publish(table, tmp_path, {}, time.perf_counter())
    write_json(tmp_path / "selection.json", {"schema_version": 1, "criteria": {}})
    with pytest.raises(ValueError, match="Stale"):
        loaders.validate_selection(tmp_path)


@pytest.mark.real_data
def test_real_membership_and_manifest():
    manifest, selected = loaders.verify_membership()
    assert len(selected) > 0
    assert len(selected) <= manifest["row_count"]
    saved = loaders.validate_selection()
    assert saved["ordered_ids"] == [row["id"] for row in selected]
    assert saved["row_indices"] == [row["row_index"] for row in selected]
