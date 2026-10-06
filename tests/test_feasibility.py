import io

import numpy as np
import pyarrow.dataset as ds
import soundfile as sf


def test_full_round_trip_against_source(native_dataset, canonical_table):
    actual = native_dataset.scanner(use_threads=False).to_table()
    # Vortex may expose Arrow string/binary view types. Normalize representations,
    # preserving required logical types and values, before comparison.
    assert actual.cast(canonical_table.schema).equals(canonical_table)


def test_native_filtered_metadata_batches(native_dataset):
    predicate = ((ds.field("duration_s") >= 3) & (ds.field("duration_s") <= 10)
                 & (ds.field("word_count") >= 5))
    scanner = native_dataset.scanner(
        columns=["row_index", "id"], filter=predicate, batch_size=2, use_threads=False
    )
    batches = list(scanner.to_batches())
    assert all(batch.schema.names == ["row_index", "id"] for batch in batches)
    assert all(batch.num_rows <= 2 for batch in batches)
    assert len(batches) >= 2
    rows = [row for batch in batches for row in batch.to_pylist()]
    assert rows == [dict(row_index=i, id=f"clip-{i}") for i in (1, 2, 5)]


def test_known_waveform_headers_and_bytes(known_audio):
    payload, expected = known_audio
    info = sf.info(io.BytesIO(payload))
    assert (info.samplerate, info.frames, info.channels) == (16000, 5, 1)
    actual, rate = sf.read(io.BytesIO(payload), dtype="float32")
    assert rate == 16000
    assert actual.dtype == np.float32
    np.testing.assert_array_equal(actual, expected)


def test_flac_codec_round_trip(known_audio):
    _, expected = known_audio
    assert "FLAC" in sf.available_formats()
    buffer = io.BytesIO()
    sf.write(buffer, expected, 16000, format="FLAC", subtype="PCM_16")
    info = sf.info(io.BytesIO(buffer.getvalue()))
    assert (info.samplerate, info.frames, info.channels) == (16000, 5, 1)
    actual, _ = sf.read(io.BytesIO(buffer.getvalue()), dtype="float32")
    np.testing.assert_array_equal(actual, expected)
