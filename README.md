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
missing prepared artifacts will fail those opted-in checks. Acquisition and
benchmark commands will be documented when implemented.

## Repository

- `tests/`: offline format and audio feasibility checks.
- `docs/milestones/`: scope contracts, bead status, and execution evidence.
- `docs/developer-experience.md`: observed setup/API friction.
- `data/`: generated inputs and provenance (ignored by Git).
- `results/`: benchmark evidence when measurement is implemented.

The baseline is 50 development clips followed by a pinned 1,000-clip LibriSpeech
subset. No model training or GPU is needed. Timing ties, regressions, and
inconclusive results are acceptable; correctness and repeatability come first.
