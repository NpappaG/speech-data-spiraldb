"""Correctness-gated, warm-up-performed local reader measurements."""
import argparse
import math
import os
import platform
import statistics
import subprocess
import time
from pathlib import Path

import torch

from common import packages, preflight, write_json
from loaders import (AUDIO_COLUMNS, CRITERIA, METADATA_COLUMNS, READER_SETTINGS, SCAN_BATCH_SIZE,
                     iter_batches, iter_records, verify_batches)


def positive_seconds(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Measured duration must be positive and finite")
    return value


def check_count(actual, expected):
    if actual != expected:
        raise ValueError(f"Wrong output count: {actual}, expected {expected}")


def measure_metadata(factory, expected_count, clock=time.perf_counter):
    start = clock()
    stream = factory()
    count = 0
    try:
        for _ in stream:
            count += 1
    finally:
        stream.close()
    elapsed = positive_seconds(clock() - start)
    check_count(count, expected_count)
    return dict(selected_count=count, selection_seconds=elapsed)


def measure_waveforms(factory, expected_count, clock=time.perf_counter):
    start = clock()
    stream = factory()
    try:
        first = next(stream, None)
        first_time = clock()
        if first is None:
            raise ValueError("Cannot measure an empty selection")
        first_count = len(first["ids"])
        if first_count <= 0:
            raise ValueError("First waveform batch is empty")
        count, batches = first_count, 1
        del first
        for batch in stream:
            count += len(batch["ids"])
            batches += 1
    finally:
        stream.close()
    end = clock()
    latency = positive_seconds(first_time - start)
    total = positive_seconds(end - start)
    if total < latency:
        raise ValueError("Invalid first-batch timing boundary")
    check_count(count, expected_count)
    remaining_count = count - first_count
    remaining = (remaining_count / positive_seconds(end - first_time) if remaining_count else None)
    return dict(selected_count=count, batch_count=batches, first_batch_count=first_count,
                first_batch_seconds=latency, total_seconds=total,
                end_to_end_clips_per_second=count / total,
                remaining_stream_clips_per_second=remaining)


def paired_order(repetitions):
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    for round_number in range(repetitions):
        formats = ["vortex", "parquet"] if round_number % 2 == 0 else ["parquet", "vortex"]
        for position, format_name in enumerate(formats):
            yield round_number + 1, position + 1, format_name


def summarize(trials):
    summary = {}
    for path in ("metadata", "waveforms"):
        summary[path] = {}
        for fmt in ("vortex", "parquet"):
            group = [trial for trial in trials if trial["path"] == path and trial["format"] == fmt]
            keys = ["selection_seconds"] if path == "metadata" else [
                "first_batch_seconds", "total_seconds", "end_to_end_clips_per_second",
                "remaining_stream_clips_per_second",
            ]
            summary[path][fmt] = {}
            for key in keys:
                values = [trial[key] for trial in group if trial[key] is not None]
                summary[path][fmt][key] = (dict(median=statistics.median(values), min=min(values), max=max(values))
                                          if values else None)
    return summary


def code_identity():
    def git(*args):
        result = subprocess.run(["git", *args], text=True, capture_output=True)
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    from common import sha256_file
    return dict(commit=git("rev-parse", "HEAD"), dirty=bool(git("status", "--porcelain")),
                source_sha256={name: sha256_file(Path(__file__).parent / name)
                               for name in ("common.py", "prepare.py", "loaders.py", "benchmark.py")})


def hardware():
    value = dict(cpu=platform.processor() or platform.machine(), logical_cpus=os.cpu_count())
    if platform.system() == "Darwin":
        for key, setting in (("cpu", "machdep.cpu.brand_string"), ("memory_bytes", "hw.memsize")):
            result = subprocess.run(["sysctl", "-n", setting], capture_output=True, text=True)
            if result.returncode == 0:
                value[key] = int(result.stdout.strip()) if key == "memory_bytes" else result.stdout.strip()
    return value


def run(data_dir="data", output="results/measurements.json", repetitions=5, batch_size=16,
        scan_batch_size=SCAN_BATCH_SIZE):
    if repetitions <= 0 or batch_size <= 0 or scan_batch_size <= 0:
        raise ValueError("repetitions and batch sizes must be positive")
    # Import/setup/hash/correctness work is outside all measured intervals.
    torch.set_num_threads(1)
    manifest = preflight(data_dir)
    gate = verify_batches(data_dir)
    expected_count = gate["selected_count"]
    identity = code_identity()
    factories = {
        "metadata": lambda fmt, sizes: iter_records(fmt, data_dir, METADATA_COLUMNS, scan_batch_size, chunk_sizes=sizes),
        "waveforms": lambda fmt, sizes: iter_batches(fmt, data_dir, batch_size, scan_batch_size, chunk_sizes=sizes),
    }
    measures = {"metadata": measure_metadata, "waveforms": measure_waveforms}
    trials = []
    for path in ("metadata", "waveforms"):
        for fmt in ("vortex", "parquet"):
            measures[path](lambda fmt=fmt: factories[path](fmt, []), expected_count)
        for round_number, position, fmt in paired_order(repetitions):
            chunk_sizes = []
            result = measures[path](lambda fmt=fmt: factories[path](fmt, chunk_sizes), expected_count)
            result["emitted_scan_chunk_sizes"] = chunk_sizes
            if path == "waveforms":
                check_count(result["batch_count"], (expected_count + batch_size - 1) // batch_size)
            result.update(path=path, format=fmt, round=round_number, position=position)
            trials.append(result)
            print(f"{path}: round {round_number}, {fmt}, {result['selected_count']} clips", flush=True)
    value = dict(
        schema_version=1,
        workload=dict(source=manifest["source"], row_count=manifest["row_count"],
                      selected_count=expected_count, selected_fraction=expected_count / manifest["row_count"],
                      criteria=CRITERIA, files=manifest["files"], preparation_settings=manifest["settings"]),
        environment=dict(os=platform.platform(), machine=platform.machine(), cpu=hardware()["cpu"], hardware=hardware(),
                         python=platform.python_version(), packages=packages(), code=identity,
                         torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads()),
        settings=dict(repetitions=repetitions, waveform_batch_size=batch_size, scan_batch_target=scan_batch_size,
                      reader_settings=READER_SETTINGS, shuffle=False, loader_processes=1,
                      projections=dict(metadata=METADATA_COLUMNS, waveforms=AUDIO_COLUMNS),
                      cache_policy="One warm-up per format/path; OS cache uncontrolled; Vortex segment cache disabled",
                      fresh_reader_per_trial=True, uses_selection_manifest=False),
        timing_boundaries=dict(
            metadata="Before open/scanner setup through full projected metadata consumption and iterator close",
            first_batch="Before fresh open through first decoded/padded waveform batch yield; no metadata pre-pass",
            total="Before fresh open through complete waveform iterator exhaustion and close",
            remaining="Clips after first batch divided by seconds from first yield through exhaustion/close; null if none",
            excluded="Imports, hash validation, correctness gate, environment discovery, downloading, preparation, JSON writes"),
        correctness_gate=gate, trials=trials, summary=summarize(trials),
        interpretation="Small local workload; report min/max variation, ties and regressions. No production or GPU claims.",
    )
    write_json(output, value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("results/measurements.json"))
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--scan-batch-size", type=int, default=SCAN_BATCH_SIZE)
    args = parser.parse_args()
    try:
        result = run(args.data_dir, args.output, args.repetitions, args.batch_size, args.scan_batch_size)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Benchmark failed: {error}\n")
    print(f"Saved {len(result['trials'])} raw trials to {args.output}")


if __name__ == "__main__":
    main()
