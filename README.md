# Speech Slices: Vortex → PyTorch Cookbook

A small local experiment comparing Vortex and Parquet: select speech metadata,
read matching encoded audio, and yield PyTorch waveform batches. This uses direct
file readers, not the Spiral platform. Implementation follows the
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
missing prepared artifacts will fail those opted-in checks. Benchmark commands will be documented when implemented.

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
poetry run pytest --real-data
```

Preparation needs network access and SoundFile FLAC support (verified by offline
tests). Default preparation streams the first 1,000 rows, never re-encodes the
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
