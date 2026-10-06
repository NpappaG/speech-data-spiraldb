# M06 Progress Report

- Status: Active
- Last updated: 2026-10-06

## Delivery summary

Beads 0–1 complete: runnable commands/contracts/results and evidence-backed experience notes consolidated; sharing/ignore/link checks passed. Bead 2 is in progress: candidate 14b3978 installed in a fresh .venv; offline tests passed with no data present before or after. Acceptance found an async Arrow shutdown hang after publication. The source path was repaired with synchronous declared-shard reads and explicit cleanup; a bounded real CLI exited normally and matched the earlier prefix. The repaired tracked candidate will be retested cleanly before completion.

## Ops notes

- Migrations: None performed.
- Env vars / secrets: None introduced.
- Deploy / rollout / rollback: No deployment performed; this is a local cookbook.

## Tests run (exact commands)

- Documentation relative-link validation: passed.
- `git check-ignore data/clips.vortex`: ignored as required.
- `git check-ignore results/measurements.json`: not ignored as required.
- Result JSON audit: no credentials or unnecessary user-home paths found.
- Clean candidate `14b3978` cloned with `git clone --no-hardlinks` to `/tmp/speech-slices-clean-14b3978`; no copied data/untracked files.
- Fresh `poetry env use /opt/homebrew/bin/python3.11` and `poetry install --no-root`: passed using the lockfile and shared package-download cache.
- `HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest -q`: 57 passed, 4 explicitly opt-in checks skipped; `test ! -e data` passed before and after.
- Acquisition/real-data/benchmark acceptance is still in progress.

## Decisions / notes

The execution contract is [scope.md](scope.md).

2026-10-06: All beads were reviewed and the scope revised before implementation; see the [planning review](../design_review.md). This is planning work only and satisfies no implementation exit criterion. Record delivery evidence and deviations here as execution proceeds.

## Outstanding / deferred

All beads and exit criteria remain outstanding. Deferred project scope is listed in the spec’s non-goals.
