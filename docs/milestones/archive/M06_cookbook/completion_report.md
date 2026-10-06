# M06 Progress Report

- Status: Complete (2026-10-06)
- Last updated: 2026-10-06

## Delivery summary

Verified the complete documented workflow from repaired clean tracked candidate 72fe87a, including fresh acquisition, 65 checks, paired measurements, and normal subprocess exits.

All beads and milestone exit criteria passed. Planning baseline: `97ab8e1`.

## Ops notes

- Migrations: None.
- Env vars / secrets: No credentials added. Generated inputs remain under ignored `data/`.
- Deploy / rollout / rollback: Local cookbook only; no deployment.

## Tests run (exact commands)

Clean checkout: `/tmp/speech-slices-clean-72fe87a`, tested commit `72fe87ab0d2a637bbea97fbbb91dd1f1d101ad5d`. Fresh project `.venv`, no copied dataset/source cache; only package-download cache was shared. All commands below ran sequentially.

- `git clone --no-hardlinks /Users/nicholaspappageorge/code/repos/github.com/NpappaG/speech-data-spiraldb /tmp/speech-slices-clean-72fe87a`: passed; tracked candidate only.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache POETRY_VIRTUALENVS_IN_PROJECT=true poetry env use /opt/homebrew/bin/python3.11`: passed.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --no-root`: lockfile installed into fresh environment.
- `test ! -e data && HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest -q && test ! -e data`: **61 passed, 4 intentionally opt-in tests skipped**; no data existed before or after.

For acquisition/integration/measurements, `HF_HOME=data/hf-cache` and `POETRY_CACHE_DIR=/tmp/speech-poetry-cache` were set. Network and hardware inspection were available; each subprocess had a 180-second deadline and exited 0:

1. `poetry run python prepare.py --limit 50 --output-dir data/dev50`: verified and terminated normally.
2. `poetry run python prepare.py`: fresh pinned 1,000-row pair verified and terminated normally.
3. `poetry run python loaders.py --verify-batches`: 178 selected clips, 12 equivalent batches.
4. `poetry run pytest --real-data -q`: **65 passed**.
5. `poetry run python benchmark.py`: 20 raw paired trials saved.
6. `poetry run python benchmark.py --output results/rerun.json`: 20 separate paired trials saved.
7. `poetry run pytest --real-data -q`: **65 passed**, including validation of the newly generated evidence.

Exact subprocess arguments, exits, elapsed times, and captured outputs are in [acceptance_commands.json](acceptance_commands.json). Clean-checkout raw evidence is retained in [acceptance_measurements.json](acceptance_measurements.json) and [acceptance_rerun.json](acceptance_rerun.json).

## Decisions / notes

The first candidate `14b3978` exposed an actual post-publication shutdown hang. Process sampling showed native Arrow thread-pool shutdown waiting after early termination of an async source scan. Explicit generator cleanup/prebuffer changes alone were insufficient. The final supported source path resolves pinned declared shard order with Hugging Face’s dataset builder, then reads synchronously with ParquetFile over HfFileSystem, with prebuffer/threads disabled and explicit file/iterator cleanup. No dependency patches, forced exits, or sleep-based workaround.

The repaired 50-row source matched the earlier prefix in every logical field and encoded audio hash. Offline regressions cover partial native-scan subprocess termination and source cleanup on success/error; full clean acquisition demonstrates the real remote path also exits normally. Hugging Face Hub is declared directly; the lock refresh changed no package versions. Historical M05 measurements retain their original code/data provenance; the acceptance artifacts record the repaired candidate.

An early verification attempt also overlapped acquisition with the offline check. It was discarded; generated temporary data was cleared and the complete no-data offline gate rerun before acquisition. Failed attempts are not counted as acceptance. README, live contributor guide, milestone links, raw evidence, and observed experience notes were reconciled. The project stopping rule is satisfied.

The delivered contract is [scope.md](scope.md). The [planning review](../../design_review.md) records the original design rationale.

## Outstanding / deferred

No outstanding work in this milestone. Deferred project scope remains excluded by the spec.
