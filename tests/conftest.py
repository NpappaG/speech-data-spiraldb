import io

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import soundfile as sf
import vortex as vx


def pytest_addoption(parser):
    parser.addoption("--real-data", action="store_true", help="Verify prepared data/ artifacts")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--real-data"):
        skip = pytest.mark.skip(reason="opt in with --real-data after preparing data")
        for item in items:
            if "real_data" in item.keywords:
                item.add_marker(skip)


@pytest.fixture
def known_audio():
    samples = np.array([0, 8192, -16384, 32767, -32768], dtype=np.int16)
    buffer = io.BytesIO()
    sf.write(buffer, samples, 16000, format="WAV", subtype="PCM_16")
    return buffer.getvalue(), samples.astype(np.float32) / 32768


@pytest.fixture
def canonical_table(known_audio):
    audio, _ = known_audio
    schema = pa.schema([
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
    return pa.Table.from_pylist([
        dict(row_index=i, id=f"clip-{i}", speaker_id=7, text="one two three four five",
             duration_s=duration, word_count=words, sample_rate=16000,
             num_frames=5, audio_bytes=audio)
        for i, (duration, words) in enumerate([
            (2.999, 5), (3.0, 5), (10.0, 5), (10.001, 5), (5.0, 4), (4.0, 6)
        ])
    ], schema=schema)


@pytest.fixture(params=["vortex", "parquet"])
def native_dataset(request, canonical_table, tmp_path):
    path = tmp_path / f"clips.{request.param}"
    if request.param == "vortex":
        vx.io.write(vx.array(canonical_table), str(path))
        return vx.open(str(path)).to_dataset()
    pq.write_table(canonical_table, path, compression="zstd")
    import pyarrow.dataset as ds
    return ds.dataset(path, format="parquet")
