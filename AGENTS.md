# Repository Guidelines

## Project Structure & Module Organization

This repository is a planned local speech-data cookbook comparing Vortex and Parquet readers that produce PyTorch batches. M01 environment and offline feasibility checks are complete. Use `docs/milestones/project_plan.md` for priorities and each milestone’s `scope.md` as its execution contract; `speech-slices-milestones.md` links to the tracking system.

The planned layout is:
- `prepare.py`: stream a pinned LibriSpeech subset and write equivalent dataset files.
- `loaders.py`: filter metadata, read selected audio, and share decoding and batching logic.
- `benchmark.py`: measure selection and batch-loading performance.
- `tests/test_equivalence.py`: verify both formats produce equivalent data and batches.
- `data/`: generated `clips.vortex` and `clips.parquet` files.
- `results/measurements.json`: raw timings and medians.
- `docs/developer-experience.md`: onboarding observations and API feedback.

## Build, Test, and Development Commands

Use Python 3.11 and Poetry; `pyproject.toml` and `poetry.lock` define dependencies. Run `poetry install --no-root` and `poetry run pytest` for offline checks. The following script commands become available as later milestones ship:
- `poetry install --no-root`: install locked dependencies.
- `poetry run python prepare.py`: prepare matching dataset files.
- `poetry run pytest`: run correctness tests.
- `poetry run python benchmark.py`: collect benchmark measurements.

Document actual arguments and prerequisites in the README as commands become available.

## Coding Style & Naming Conventions

Use four-space indentation and standard Python conventions: `snake_case` for modules, functions, and variables; `PascalCase` for classes. Keep preparation, selection, decoding, and timing responsibilities separate. No formatter or linter is configured; document any tooling introduced in `pyproject.toml`.

## Testing Guidelines

Use pytest with `tests/test_*.py` files and `test_*` functions. No coverage threshold is established. Check each reader against independent fixtures before cross-format equivalence. Verify ordered IDs, metadata, audio bytes, waveform values, lengths, and lazy decoding. Cover a nonempty filtered subset, consistent sample rates, and final partial batches. Default tests must be offline; opt into real-data verification explicitly. Develop with 50 examples before the 1,000-example subset.

## Commit & Pull Request Guidelines

Git history contains only `Initial commit`, so no commit convention is established. Use concise, imperative messages describing one coherent change. PRs should explain behavior, relevant milestones, validation commands and outcomes, and reproducibility impacts. Benchmark claims must include timing boundaries, package versions, hardware, cache conditions, and raw results.

## Data & Scope

Pin dataset revisions and preserve source order. Ignore downloaded audio and generated dataset files before creating them. Keep credentials out of Git. Exclude downloads and preparation from benchmark timing; use identical decoding and batching for both formats. Treat small-run timings as cookbook evidence; no speedup is required. Defer model training, cloud services, and multi-worker tuning.

## Milestone Tracking

Follow `docs/milestones/README.md`. On starting work, mark the scope, report, and dashboard Active. Record shipped changes and exact validation commands/results in `completion_report.md`; maintain runnable commands and observed experience notes as work ships. On completion, mark Complete with the date, update dashboard outcomes and the index, move the folder into `docs/milestones/archive/`, and repair links. Do not reimplement completed milestones unless explicitly asked.
