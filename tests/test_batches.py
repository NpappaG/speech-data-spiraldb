import io

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import soundfile as sf
import torch
import vortex as vx

import loaders


def encoded_record(index, frames=5, rate=16000, channels=1):
    samples = (np.arange(frames, dtype=np.int16) * 256)
    if channels > 1:
        samples = np.tile(samples[:, None], (1, channels))
    buffer = io.BytesIO()
    sf.write(buffer, samples, rate, format="WAV", subtype="PCM_16")
    return dict(id=f"clip-{index}", text=f"transcript {index}", audio_bytes=buffer.getvalue(),
                num_frames=frames, sample_rate=rate)


def test_decoder_against_known_samples(known_audio):
    payload, expected = known_audio
    record = dict(id="known", audio_bytes=payload, num_frames=5, sample_rate=16000)
    np.testing.assert_array_equal(loaders.decode_record(record), expected)


@pytest.mark.parametrize("fault", ["stereo", "rate", "metadata_rate", "frames", "corrupt", "empty"])
def test_decoder_rejects_invalid_records(fault):
    record = encoded_record(0, channels=2 if fault == "stereo" else 1,
                            rate=8000 if fault == "rate" else 16000,
                            frames=0 if fault == "empty" else 5)
    if fault == "metadata_rate":
        record["sample_rate"] = 8000
    elif fault == "frames":
        record["num_frames"] = 6
    elif fault == "corrupt":
        record["audio_bytes"] = b"bad"
    with pytest.raises(ValueError, match="Clip clip-0:"):
        loaders.decode_record(record)


@pytest.mark.parametrize("count", [0, 1, 16, 17])
def test_batch_contract_padding_and_partial_batch(count):
    records = [encoded_record(i, frames=5 + i % 3) for i in range(count)]
    batches = list(loaders.batch_records(iter(records)))
    assert len(batches) == (count + 15) // 16
    assert [clip for batch in batches for clip in batch["ids"]] == [row["id"] for row in records]
    for batch in batches:
        assert batch["waveforms"].dtype == torch.float32
        assert batch["lengths"].dtype == torch.int64
        assert batch["waveforms"].device.type == "cpu"
        assert batch["sample_rate"] == 16000
        for i, clip_id in enumerate(batch["ids"]):
            index = int(clip_id.split("-")[1])
            length = 5 + index % 3
            assert batch["lengths"][i] == length
            assert batch["transcripts"][i] == f"transcript {index}"
            torch.testing.assert_close(batch["waveforms"][i, :length],
                                       torch.arange(length, dtype=torch.float32) / 128,
                                       rtol=0, atol=0)
            assert torch.count_nonzero(batch["waveforms"][i, length:]) == 0
    if count == 17:
        assert len(batches[-1]["ids"]) == 1


def test_lazy_decode_and_early_cleanup(monkeypatch):
    decoded, closed = [], []
    original = loaders.decode_record
    def decoder(record):
        decoded.append(record["id"])
        return original(record)
    def source():
        try:
            for i in range(17):
                yield encoded_record(i)
        finally:
            closed.append(True)
    monkeypatch.setattr(loaders, "decode_record", decoder)
    batches = loaders.batch_records(source())
    assert decoded == []
    assert len(next(batches)["ids"]) == 16
    assert decoded == [f"clip-{i}" for i in range(16)]
    batches.close()
    assert closed == [True]


@pytest.mark.parametrize("fmt", ["vortex", "parquet"])
@pytest.mark.parametrize("scan_size", [1, 3, 64])
def test_chunk_independence_and_no_rejected_decoding(fmt, scan_size, tmp_path, monkeypatch):
    rows = []
    for i in range(18):
        row = encoded_record(i, frames=5 + i % 3)
        row.update(row_index=i, speaker_id=7, duration_s=4.0 if i < 17 else 11.0, word_count=5)
        if i == 17:
            row["audio_bytes"] = b"rejected corrupt audio must never decode"
        rows.append(row)
    table = pa.Table.from_pylist(rows)
    if fmt == "vortex":
        vx.io.write(vx.array(table), str(tmp_path / "clips.vortex"))
    else:
        pq.write_table(table, tmp_path / "clips.parquet")
    original, decoded = loaders.decode_record, []
    def spy(record):
        decoded.append(record["id"])
        return original(record)
    monkeypatch.setattr(loaders, "decode_record", spy)
    batches = list(loaders.iter_batches(fmt, tmp_path, scan_batch_size=scan_size))
    assert [len(batch["ids"]) for batch in batches] == [16, 1]
    assert decoded == [f"clip-{i}" for i in range(17)]
    assert batches[0]["lengths"].tolist() == [5 + i % 3 for i in range(16)]


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_batch_size(size):
    with pytest.raises(ValueError, match="positive"):
        list(loaders.batch_records([], batch_size=size))


@pytest.mark.real_data
def test_complete_real_batch_equivalence():
    result = loaders.verify_batches()
    assert result["selected_count"] == 178
    assert result["batch_count"] == 12
