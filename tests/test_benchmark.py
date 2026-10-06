import pytest

from benchmark import measure_metadata, measure_waveforms, paired_order, summarize


class Stream:
    def __init__(self, values):
        self.iterator = iter(values)
        self.closed = False
    def __iter__(self):
        return self
    def __next__(self):
        return next(self.iterator)
    def close(self):
        self.closed = True


def clock(values):
    return iter(values).__next__


def test_metadata_consumption_and_open_boundary():
    events = []
    stream = Stream([{}, {}, {}])
    times = iter([10, 15])
    def timer():
        events.append("clock")
        return next(times)
    def factory():
        events.append("open")
        return stream
    result = measure_metadata(factory, 3, timer)
    assert result == dict(selected_count=3, selection_seconds=5)
    assert events == ["clock", "open", "clock"]
    assert stream.closed


def test_waveform_metric_denominators():
    stream = Stream([dict(ids=list(range(16))), dict(ids=[16])])
    result = measure_waveforms(lambda: stream, 17, clock([10, 12, 20]))
    assert result["first_batch_seconds"] == 2
    assert result["total_seconds"] == 10
    assert result["end_to_end_clips_per_second"] == 1.7
    assert result["remaining_stream_clips_per_second"] == 1 / 8
    assert result["batch_count"] == 2 and stream.closed


def test_one_batch_remaining_rate_is_null():
    result = measure_waveforms(lambda: Stream([dict(ids=["a"])]), 1, clock([0, 1, 2]))
    assert result["remaining_stream_clips_per_second"] is None


def test_empty_selection_rejected_and_closed():
    stream = Stream([])
    with pytest.raises(ValueError, match="empty selection"):
        measure_waveforms(lambda: stream, 0, clock([0, 1]))
    assert stream.closed


@pytest.mark.parametrize("times", [[0, 0], [2, 1], [0, float("nan")]])
def test_invalid_metadata_duration(times):
    with pytest.raises(ValueError, match="positive and finite"):
        measure_metadata(lambda: Stream([{}]), 1, clock(times))


def test_wrong_counts_and_waveform_time():
    with pytest.raises(ValueError, match="Wrong output count"):
        measure_metadata(lambda: Stream([{}]), 2, clock([0, 1]))
    with pytest.raises(ValueError, match="Wrong output count"):
        measure_waveforms(lambda: Stream([dict(ids=["a"])]), 2, clock([0, 1, 2]))
    with pytest.raises(ValueError, match="positive and finite"):
        measure_waveforms(lambda: Stream([dict(ids=["a"])]), 1, clock([0, 0, 1]))


def test_default_paired_order_and_summary():
    order = list(paired_order(5))
    assert len(order) == 10
    assert [fmt for round_number, position, fmt in order if position == 1] == [
        "vortex", "parquet", "vortex", "parquet", "vortex"
    ]
    assert sum(fmt == "vortex" for _, _, fmt in order) == 5
    trials = []
    for path in ("metadata", "waveforms"):
        for round_number, position, fmt in order:
            values = dict(selection_seconds=float(round_number)) if path == "metadata" else dict(
                first_batch_seconds=1., total_seconds=2., end_to_end_clips_per_second=3.,
                remaining_stream_clips_per_second=None)
            trials.append(dict(path=path, format=fmt, **values))
    result = summarize(trials)
    assert result["metadata"]["vortex"]["selection_seconds"] == dict(median=3., min=1., max=5.)
    assert result["waveforms"]["parquet"]["remaining_stream_clips_per_second"] is None
    with pytest.raises(ValueError, match="positive"):
        list(paired_order(0))
