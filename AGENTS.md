# Repository Guidelines

## Project Structure & Module Organization

This is a local Vortex-to-PyTorch speech cookbook with a Parquet comparison.
`prepare.py` streams a pinned LibriSpeech prefix and publishes equivalent files;
`loaders.py` performs native filtering and shared decoding/batching;
`benchmark.py` collects correctness-gated timings. `common.py` defines schema,
provenance, and explicit artifact preflight checks.

`tests/` contains generated-fixture tests plus opt-in real-data checks.
`data/` holds ignored audio files, manifests, and acquisition caches.
`results/` contains tracked raw measurement evidence. `docs/developer-experience.md`
records observed integration friction. Milestone contracts and reports live under
`docs/milestones/`, with completed work in `archive/`.

## Build, Test, and Development Commands

Use Python 3.11 and Poetry; commit dependency changes with `poetry.lock`.

- `poetry install --no-root`: install locked runtime/test dependencies.
- `poetry run pytest`: run offline generated-fixture tests.
- `poetry run python prepare.py --limit 50 --output-dir data/dev50`: prepare a development prefix.
- `poetry run python prepare.py`: prepare the pinned 1,000-row delivery subset.
- `poetry run python loaders.py --verify-batches`: save membership and verify complete batch equivalence.
- `poetry run pytest --real-data`: require prepared data and verify integration/evidence.
- `poetry run python benchmark.py`: save paired measurements after the correctness gate.

Use fresh output paths or explicitly request preparation overwrite. Keep exact
commands and prerequisites current in the README.

## Coding Style & Naming Conventions

Use four spaces, `snake_case` modules/functions/variables, and `PascalCase` classes.
Keep preparation, scanning, decoding, and timing separate. No formatter or linter
is configured; document new tooling in `pyproject.toml`.

## Testing Guidelines

Use pytest `tests/test_*.py` files and `test_*` functions. No coverage threshold
is established. Verify readers independently before cross-format equality.
Cover predicate boundaries, empty selections, artifact identity, known waveforms,
padding, partial batches, lazy decoding, and timing arithmetic. Default tests
must require neither network nor downloaded data; opt-in missing data must fail.

## Commit & Pull Request Guidelines

Use concise imperative commits for coherent checkpoints. PRs should explain
behavior, milestone scope, exact validation outcomes, and reproducibility impacts.
Include raw evidence and cache/hardware/version context for benchmark claims.

## Milestone & Scope Rules

Follow `docs/milestones/README.md`: mark work Active, check tasks as evidence
passes, and record commands/results. On completion, date scope/report, update
indexes/dashboard, archive the folder, and repair links. Do not reimplement
completed milestones unless explicitly asked. Keep generated audio and credentials
out of Git. Small local timings require no speedup; training, cloud infrastructure,
and Spiral integration remain deferred.
