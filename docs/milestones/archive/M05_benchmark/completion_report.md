# M05 Progress Report

- Status: Complete (2026-10-06)
- Last updated: 2026-10-06

## Delivery summary

Saved two correctness-gated invocations with 20 raw trials each; metadata and remaining-stream differences are inconclusive, while first-batch and total times were lower for Vortex in these runs.

All beads and milestone exit criteria passed. Planning baseline: `97ab8e1`.

## Ops notes

- Migrations: None.
- Env vars / secrets: No credentials added. Generated inputs remain under ignored `data/`.
- Deploy / rollout / rollback: Local cookbook only; no deployment.

## Tests run (exact commands)

- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest --real-data -q`: **61 passed**, including recorded-trial order/count/rate/summary checks.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python benchmark.py --output results/measurements.json`: passed with approved hardware inspection; 20 trials saved (five per format/path).
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python benchmark.py --output results/rerun.json`: passed independently with approved hardware inspection; 20 more trials saved.
- `sysctl -n machdep.cpu.brand_string hw.memsize`: Apple M1, 17,179,869,184 bytes RAM.
- `git diff --check`: passed.

## Decisions / notes

Timing code checkpoint: `39e5680`; raw results also record exact source hashes and actual dirty-worktree state. CPU operations use one PyTorch intra-op thread; inter-op thread count and scanner controls are recorded. Reader/scanner open and full iteration belong inside timers. Hash/correctness/import/JSON work is excluded. No persisted membership or decoded data is reused.

A preliminary sandbox run lacked CPU/RAM details; it was replaced by a complete hardware-recorded run. Cache policy remains one warm-up per format/path, OS cache uncontrolled, Vortex segment cache disabled. Actual filtered scan chunk sizes are recorded for every trial; no physical-I/O claim is inferred.

Primary medians: metadata 3.018 / 3.309 ms (Vortex/Parquet), first batch 60.583 / 149.680 ms, total 282.156 / 372.985 ms, end-to-end 630.856 / 477.231 clips/s. Rerun: first batch 68.273 / 185.500 ms, total 301.407 / 425.594 ms. Metadata and remaining-stream median differences are smaller than observed variation. Both invocations show a startup/total-time difference for this local reader configuration only. The README gives min/max ranges and all limitations; ties, regressions, or inconclusive results would also satisfy this milestone.

The delivered contract is [scope.md](scope.md). The [planning review](../../design_review.md) records the original design rationale.

## Outstanding / deferred

No outstanding work in this milestone. Deferred project scope remains excluded by the spec.
