import io
import json
import time

import numpy as np
import pytest
import soundfile as sf

from common import preflight, sha256_bytes
from prepare import build_table, canonical_record, publish, read_table


def source_record(payload, clip_id="a", text=" one\t two\n three "):
    return dict(id=clip_id, speaker_id=7, text=text, audio={"bytes": payload, "path": None})


def test_headers_metadata_and_original_bytes(known_audio):
    payload, _ = known_audio
    row = canonical_record(source_record(payload), 0)
    assert row["audio_bytes"] == payload
    assert row["duration_s"] == 5 / 16000
    assert row["word_count"] == 3
    assert row["num_frames"] == 5
    assert row["row_index"] == 0


@pytest.mark.parametrize("rate,channels", [(8000, 1), (16000, 2)])
def test_invalid_audio_shape(rate, channels):
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros((4, channels)), rate, format="WAV")
    with pytest.raises(ValueError, match="Clip bad:.*mono 16 kHz"):
        canonical_record(source_record(buffer.getvalue(), "bad"), 0)


@pytest.mark.parametrize("payload", [b"", b"corrupt"])
def test_invalid_bytes(payload):
    with pytest.raises(ValueError, match="Clip bad:"):
        canonical_record(source_record(payload, "bad"), 0)


def test_duplicate_missing_and_short_source(known_audio):
    payload, _ = known_audio
    record = source_record(payload)
    with pytest.raises(ValueError, match="duplicate ID"):
        build_table([record, record], 2)
    with pytest.raises(ValueError, match="Source exhausted"):
        build_table([record], 2)
    with pytest.raises(ValueError, match="positive"):
        build_table([record], 0)
    with pytest.raises(ValueError, match="not accessible"):
        canonical_record(source_record(None), 0)
    with pytest.raises(ValueError, match="invalid transcript"):
        canonical_record(source_record(payload, text=None), 0)


def test_bounded_consumption(known_audio):
    payload, _ = known_audio
    def records():
        yield source_record(payload)
        raise AssertionError("Consumed beyond requested prefix")
    assert build_table(records(), 1).num_rows == 1


def test_publication_and_stale_detection(known_audio, tmp_path):
    payload, _ = known_audio
    table = build_table([source_record(payload)], 1)
    publish(table, tmp_path, {"revision": "a" * 40}, time.perf_counter())
    manifest = preflight(tmp_path)
    assert manifest["audio_sha256"] == [sha256_bytes(payload)]
    for fmt in ("vortex", "parquet"):
        assert read_table(tmp_path / f"clips.{fmt}", fmt).equals(table)
    with pytest.raises(ValueError, match="exist"):
        publish(table, tmp_path, {}, time.perf_counter())
    path = tmp_path / "clips.parquet"
    path.write_bytes(path.read_bytes() + b"altered")
    with pytest.raises(ValueError, match="Stale"):
        preflight(tmp_path)
    publish(table, tmp_path, {"revision": "a" * 40}, time.perf_counter(), overwrite=True)
    assert preflight(tmp_path)["row_count"] == 1


def test_failed_publication_has_no_valid_manifest(known_audio, tmp_path, monkeypatch):
    from pathlib import Path
    payload, _ = known_audio
    table = build_table([source_record(payload)], 1)
    publish(table, tmp_path, {}, time.perf_counter())
    real_replace = Path.replace
    def interrupted(path, target):
        if path.name == "clips.parquet":
            raise OSError("simulated interruption")
        return real_replace(path, target)
    monkeypatch.setattr(Path, "replace", interrupted)
    with pytest.raises(OSError, match="interruption"):
        publish(table, tmp_path, {}, time.perf_counter(), overwrite=True)
    with pytest.raises(ValueError, match="Missing"):
        preflight(tmp_path)


@pytest.mark.real_data
def test_prepared_real_data():
    from pathlib import Path
    directory = Path("data")
    manifest = preflight(directory)
    assert manifest["row_count"] == 1000
    tables = [read_table(directory / f"clips.{fmt}", fmt) for fmt in ("vortex", "parquet")]
    for table in tables:
        assert table["id"].to_pylist() == manifest["ordered_ids"]
        assert [sha256_bytes(payload) for payload in table["audio_bytes"].to_pylist()] == manifest["audio_sha256"]
        for row in table.to_pylist():
            source = source_record(row["audio_bytes"], row["id"], row["text"])
            source["speaker_id"] = row["speaker_id"]
            assert canonical_record(source, row["row_index"]) == row
    assert tables[0].equals(tables[1])


def test_missing_id_and_zero_frames(known_audio):
    payload, _ = known_audio
    record = source_record(payload)
    del record["id"]
    with pytest.raises(ValueError, match="invalid ID"):
        canonical_record(record, 0)
    buffer = io.BytesIO()
    sf.write(buffer, np.array([], dtype=np.float32), 16000, format="WAV")
    with pytest.raises(ValueError, match="nonempty"):
        canonical_record(source_record(buffer.getvalue()), 0)


@pytest.mark.parametrize("limit", [1, 2])
def test_partial_source_iterator_closed_on_success_and_error(known_audio, limit):
    payload, _ = known_audio
    closed = []
    def records():
        try:
            yield source_record(payload)
            raise ValueError("source failure")
        finally:
            closed.append(True)
    if limit == 1:
        assert build_table(records(), limit).num_rows == 1
    else:
        with pytest.raises(ValueError, match="source failure"):
            build_table(records(), limit)
    assert closed == [True]


def test_synchronous_source_prefix_order_and_file_close(known_audio, tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from prepare import stream_source_files
    payload, _ = known_audio
    closed = []
    class Filesystem:
        def open(self, path, mode):
            stream = open(path, mode)
            closed.append(stream)
            return stream
    paths = []
    for i in range(2):
        path = tmp_path / f"{i}.parquet"
        rows = [source_record(payload, f"{i}-{j}") for j in range(70)]
        pq.write_table(pa.Table.from_pylist(rows), path, row_group_size=35)
        paths.append(str(path))
    table = build_table(stream_source_files(paths, Filesystem()), 75)
    assert table["id"].to_pylist() == [f"0-{j}" for j in range(70)] + [f"1-{j}" for j in range(5)]
    assert all(stream.closed for stream in closed)


def test_partial_source_scan_subprocess_terminates(known_audio, tmp_path):
    import subprocess
    import sys
    import pyarrow as pa
    import pyarrow.parquet as pq
    payload, _ = known_audio
    path = tmp_path / "source.parquet"
    pq.write_table(pa.Table.from_pylist([source_record(payload, str(i)) for i in range(140)]), path, row_group_size=35)
    code = '''from prepare import stream_source_files, build_table
import sys
class Filesystem:
    def open(self, path, mode):
        return open(path, mode)
print(build_table(stream_source_files([sys.argv[1]], Filesystem()), 5).num_rows)
'''
    result = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True,
                            text=True, timeout=20, check=True)
    assert result.stdout.strip() == "5"
