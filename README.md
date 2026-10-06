# Speech Slices: Vortex → PyTorch Cookbook

A small local experiment comparing Vortex and Parquet: select speech metadata,
read matching encoded audio, and yield PyTorch waveform batches. This uses direct
file readers, not the Spiral platform. Execution evidence is recorded in the
[milestone dashboard](docs/milestones/project_plan.md).

## Setup

Use a healthy **Python 3.11** interpreter and Poetry (tested with 1.5.1).
On this development machine the interpreter is `/opt/homebrew/bin/python3.11`;
replace that path with your own Python 3.11 executable.

```sh
poetry env use /opt/homebrew/bin/python3.11
poetry install --no-root
poetry run pytest
```

The lockfile pins dependencies. Installation needs network access; the default
suite generates fixtures in temporary directories and needs no dataset or
network. Future real-data tests require explicit `--real-data` and preparation;
missing prepared artifacts will fail those opted-in checks. Benchmark commands and timing boundaries are below.

## Repository

- `tests/`: offline format and audio feasibility checks.
- `docs/milestones/`: scope contracts, bead status, and execution evidence.
- `docs/developer-experience.md`: observed setup/API friction.
- `data/`: generated inputs and provenance (ignored by Git).
- `results/`: benchmark evidence when measurement is implemented.

The baseline is 50 development clips followed by a pinned 1,000-clip LibriSpeech
subset. No model training or GPU is needed. Timing ties, regressions, and
inconclusive results are acceptable; correctness and repeatability come first.

## Prepare the source

The default source is `openslr/librispeech_asr`, `clean` / `train.100`, pinned at
`71cacbfb7e2354c4226d01e70d77d5fca3d04ba1`. Source audio is preserved as encoded
bytes; header inspection establishes mono 16 kHz audio, frame counts, and duration.
Word count is `len(text.split())`. Source IDs are unique and `row_index` preserves
zero-based source order. The dataset card lists CC BY 4.0; see the
[LibriSpeech source and attribution](https://huggingface.co/datasets/openslr/librispeech_asr).

```sh
poetry run python prepare.py --limit 50 --output-dir data/dev50
poetry run python prepare.py
poetry run python loaders.py --verify-batches
poetry run pytest --real-data
```

Preparation needs network access and SoundFile FLAC support (verified by offline
tests). Hugging Face `datasets` resolves the pinned, ordered source shard list;
a synchronous PyArrow `ParquetFile` iterator reads encoded records in 64-row
batches with threads/prebuffer disabled. The source iterator and file handles
are closed even when the requested prefix stops partway through a shard. This
avoids an observed async Arrow shutdown hang without decoding/re-encoding audio. Default preparation streams the first 1,000 rows, never re-encodes the
audio, and writes `data/clips.vortex`, `data/clips.parquet` (Zstandard), and
`data/preparation.json`. The manifest records ordered IDs, original audio hashes,
source revision, schema, settings, package versions, file hashes/sizes, and elapsed
time. Streaming can fetch extra shard bytes beyond the requested rows.

Use a fresh `--output-dir`, or explicitly pass `--overwrite` to replace artifacts.
Outputs are verified against the canonical source table before publication;
provenance is published last. Interrupted replacement leaves no valid manifest,
and downstream preflight rejects mismatched hashes. Tests opted into with
`--real-data` require the 1,000-row subset at `data/` and fail when it is absent.
Changing `--revision` resolves and records a new immutable source commit.

## Select clips

```sh
poetry run python loaders.py
poetry run pytest --real-data
```

Both readers use native scans with inclusive `3 <= duration_s <= 10` and
`word_count >= 5`. `data/selection.json` records independently verified ordered
membership and source/file identity. It is provenance, not a precomputed shortcut
for benchmarks or waveform loading.

```python
from common import preflight
from loaders import select_metadata, iter_audio_records

preflight("data")  # expensive hash validation, outside timing
metadata = select_metadata("vortex", "data")  # audio column excluded
records = iter_audio_records("parquet", "data")  # fresh filtered scan, lazy
try:
    first = next(records)
finally:
    records.close()
```

Metadata projection returns source index/ID, speaker, text, duration, and word
count. Audio records return index/ID, transcript, sample rate/frame count, and
encoded bytes. Scans target 64 rows per chunk, disable reader threads, disable
Vortex segment caching, and disable PyArrow batch/fragment readahead. Vortex has
no public explicit-close API in this version; generator completion/closing
releases reader references. Always close iterators stopped early.

Storage may still fetch or decompress chunks containing rejected rows. Avoiding
waveform decoding is a logical guarantee; exact physical I/O savings are not
measured here.

## Produce PyTorch batches

```sh
poetry run python loaders.py --verify-batches
```

```python
from common import preflight
from loaders import iter_batches

preflight("data")
batches = iter_batches("vortex", "data", batch_size=16)
try:
    for batch in batches:
        waveforms = batch["waveforms"]  # CPU float32 [B, maximum samples in batch]
        lengths = batch["lengths"]      # int64 [B], original lengths in samples
        # batch["ids"], batch["transcripts"], batch["sample_rate"] (16000)
finally:
    batches.close()
```

The shared decoder preserves mono float32 waveform samples and validates actual
rate/frame counts against metadata. There is no resampling, channel mixing,
normalization, augmentation, shuffle, or persistent decoded cache. Padding is
zero; the final partial batch is retained. Empty selections yield zero batches;
invalid audio fails with its clip ID. Batches span scanner chunk boundaries and
decode only matching clips once per iteration. The selected 178 clips yield 12
batches at size 16, ending with two clips. The same contract is checked against
known samples and across both complete real-data readers.

## Measure

```sh
poetry run python benchmark.py
poetry run python benchmark.py --output results/rerun.json
poetry run pytest --real-data
```

The harness runs a full file/membership/waveform correctness gate before timing.
Each path has one warm-up per format, then five paired rounds alternating format
order (20 raw trials per invocation). Each trial opens a fresh reader; no prepared
membership, open scanner, or decoded waveform is reused. CPU waveform operations
use one PyTorch intra-op thread; scans disable reader threads. JSON writes,
imports, integrity checks, downloads, and preparation are outside timing.

- Metadata latency starts before opening/scanner setup and ends after consuming
  all projected selected metadata and closing the iterator.
- First-batch latency starts before a fresh filtered audio scan and ends at the
  first decoded/padded batch. There is no metadata pre-pass.
- Total time includes opening, scanning, decoding, padding, and full exhaustion.
  End-to-end clips/s divides all selected clips by that time.
- Remaining-stream clips/s divides clips after the first batch by time after its
  yield through exhaustion/close. It is null when no clips remain.

Outputs record raw timings, medians/min/max, actual emitted scan chunk sizes,
source/file/code hashes, dirty Git state, versions, hardware, and reader settings.
The cache policy is **warm-up performed; OS cache uncontrolled**. No cold-cache
claim is made. `--repetitions`, `--batch-size`, and `--scan-batch-size` configure
both formats equally; `--data-dir` selects an input pair. `--output` replaces the
named result JSON; use a separate path to preserve an earlier run.

## Observed results

Apple M1, 16 GiB RAM, 8 logical CPUs, macOS 26.6.2, Python 3.11.15;
1,000 source clips, 178 selected, batch size 16, scan target 64. Vortex 0.87.0,
PyArrow 25.0.1, PyTorch 2.14.1, SoundFile 0.13.1. Complete package/code/settings
provenance is in [primary measurements](results/measurements.json) and the
[independent rerun](results/rerun.json). Numbers below are medians; latency/time
cells include the observed min–max range, not a confidence interval.

### Primary run

| Metric | Vortex | Parquet |
| --- | ---: | ---: |
| Metadata latency | 3.0 (2.1–3.5) ms | 3.3 (2.5–3.9) ms |
| First batch | 60.6 (60.0–64.9) ms | 149.7 (126.0–203.2) ms |
| Complete iteration | 282.2 (277.8–293.2) ms | 373.0 (352.5–422.4) ms |
| End-to-end throughput | 630.9 (607.0–640.8) clips/s | 477.2 (421.4–504.9) clips/s |
| Remaining-stream throughput | 729.9 (709.6–744.0) clips/s | 715.2 (654.7–738.9) clips/s |

### Separate rerun

| Metric | Vortex | Parquet |
| --- | ---: | ---: |
| Metadata latency | 6.3 (4.4–16.2) ms | 9.7 (5.5–12.3) ms |
| First batch | 68.3 (63.1–77.5) ms | 185.5 (120.0–197.9) ms |
| Complete iteration | 301.4 (286.5–349.7) ms | 425.6 (344.3–428.1) ms |
| End-to-end throughput | 590.6 (509.1–621.3) clips/s | 418.2 (415.8–517.0) clips/s |
| Remaining-stream throughput | 700.0 (595.1–733.3) clips/s | 697.9 (638.6–722.3) clips/s |

Metadata differences and remaining-stream throughput are inconclusive relative
to observed variation. Vortex had lower first-batch latency and complete-iteration
time in both invocations. The similar remaining-stream rates show why selection,
startup, and complete loading must be reported separately. This is an observation
of these readers/settings/files, not a general format ranking or causal proof.

The 1,000-row prefix is small and source-ordered, not a representative randomized
production corpus. Encoded audio decoding is shared; physical writer layouts and
compression defaults differ. Vortex is larger here (226,064,756 bytes versus
217,925,013 for Parquet). We did not measure physical bytes read, GPU utilization,
training speed, distributed loading, or Spiral’s platform features. Larger sizes,
selectivity sweeps, and I/O counters are separate future experiments.

## Troubleshooting

- Installation/import/hash failures: verify the chosen Python 3.11 interpreter;
  `poetry env info` should point to this repository’s environment.
- Missing/stale artifacts: prepare the subset, then regenerate selection. Use a
  fresh directory or `--overwrite`; do not mix files from different preparations.
- Source access failures: check network access and the pinned revision. Public
  Hub requests need no token; client rate-limit suggestions are informational.
- Audio failures: check FLAC availability (`poetry run pytest` tests it). Invalid
  clips report their IDs rather than being silently resampled or skipped.
- Missing CPU/RAM metadata in a restricted runner: inspect the saved environment
  record. This development sandbox required approved hardware inspection for a
  complete record; do not invent unavailable hardware details.

See [developer experience](docs/developer-experience.md) for observed integration
friction and concrete documentation/API suggestions.

## Clean-checkout verification

The complete workflow was verified from tracked candidate `72fe87a` in a fresh
project environment, with no copied data/source cache. Default offline checks:
61 passed, four explicitly opt-in tests skipped. Fresh acquisition, batch
equivalence, both measurements, and final integration/evidence checks passed
(65 tests). Every CLI subprocess exited normally under a deadline. See the
[M06 acceptance report](docs/milestones/archive/M06_cookbook/completion_report.md)
for exact commands, failed-attempt repairs, environment details, and raw evidence.
