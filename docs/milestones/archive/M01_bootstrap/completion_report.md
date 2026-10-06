# M01 Progress Report

- Status: Complete (2026-10-06)
- Last updated: 2026-10-06

## Delivery summary

Locked the Python 3.11 environment and verified both native scanners plus known-sample WAV/FLAC decoding.

All beads and milestone exit criteria passed. Planning baseline: `97ab8e1`.

## Ops notes

- Migrations: None.
- Env vars / secrets: No credentials added. Generated inputs remain under ignored `data/`.
- Deploy / rollout / rollback: Local cookbook only; no deployment.

## Tests run (exact commands)

- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry lock`: passed after network escalation (sandbox DNS failed).
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry install --no-root`: passed; 50 installs and one environment-local update.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest -q`: **6 passed**.
- `git check-ignore data/clips.vortex data/preparation.json .venv/example .pytest_cache/example temporary.tmp`: all ignored.
- `git check-ignore results/measurements.json docs/developer-experience.md`: exit 1 as expected, neither ignored.
- `git diff --check`: passed.
- `poetry run python` import/codec probe: all planned packages import; FLAC available.

## Decisions / notes

Python 3.11.15 / macOS 26.6.2 arm64; Poetry 1.5.1. Locked versions: Vortex 0.87.0, PyArrow 25.0.1, torch 2.14.1, datasets 5.1.0, SoundFile 0.13.1, NumPy 2.4.6, pytest 9.1.1.

Verified `vx.io.write(vx.array(table), path)`, `vx.open(path).to_dataset().scanner(columns=..., filter=..., batch_size=2, use_threads=False).to_batches()` and equivalent PyArrow Dataset scans. Both yield bounded batches in source order. Vortex Arrow string/binary views are normalized to canonical logical types for comparison; payloads and values remain exact. No empty module skeletons or Hugging Face Vortex reader dependency introduced.

The delivered contract is [scope.md](scope.md). The [planning review](../../design_review.md) records the original design rationale.

## Outstanding / deferred

No outstanding work in this milestone. Deferred project scope remains excluded by the spec.
