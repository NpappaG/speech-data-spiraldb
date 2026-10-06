# Project Plan (Macro Burndown)

- Status: Living plan
- Created: 2026-10-06
- Last updated: 2026-10-06

## Vision

A small local Vortex cookbook: filter speech metadata, decode selected audio, and yield PyTorch batches. Compare with Parquet on identical data. Correctness and reproducibility matter more than a speedup; this does not test the Spiral platform.

## Active milestones


## Planned milestones



### M05 – Measure without overstating results

- Status: Planned
- Why: Collect honest timings after correctness passes.
- Progress: Scope reviewed; no implementation.
- Next: Check timing arithmetic; run warm-ups, paired trials, and a rerun.
- Risks/Blocks: Tiny-workload noise and OS caching; depends on M04.
- See: [scope](M05_benchmark/scope.md)

### M06 – Package the cookbook

- Status: Planned
- Why: Make the documented experiment repeatable by another developer.
- Progress: Scope reviewed; no implementation.
- Next: Consolidate accumulated docs and verify a clean tracked checkout.
- Risks/Blocks: Hidden local prerequisites; depends on M05.
- See: [scope](M06_cookbook/scope.md)

## Completed milestones

- M04 – Produce real PyTorch batches: Complete (2026-10-06). Both readers produce identical complete waveform batches: 178 clips in 12 batches, with correct zero padding and a two-clip final batch. [Scope](archive/M04_pytorch_batches/scope.md) · [Report](archive/M04_pytorch_batches/completion_report.md)
- M03 – Select a reproducible training subset: Complete (2026-10-06). Verified 178 selected clips (17.8%) against an independent metadata predicate, with native lazy scans and content-linked membership provenance. [Scope](archive/M03_subset_selection/scope.md) · [Report](archive/M03_subset_selection/completion_report.md)
- M02 – Prepare one dataset in two formats: Complete (2026-10-06). Published and independently verified the pinned 1,000-row dataset pair; repeated 50-row preparations have identical logical contents. [Scope](archive/M02_dataset_preparation/scope.md) · [Report](archive/M02_dataset_preparation/completion_report.md)
- M01 – Bootstrap and smoke-test: Complete (2026-10-06). Locked the Python 3.11 environment and verified both native scanners plus known-sample WAV/FLAC decoding. [Scope](archive/M01_bootstrap/scope.md) · [Report](archive/M01_bootstrap/completion_report.md)


## Future candidates / parking lot

Larger datasets, selectivity sweeps, and physical-I/O instrumentation require separate follow-up scope. Model training, multi-worker tuning, cloud storage, dashboards, and Spiral integration remain deferred. Stop with correct batches, saved measurements (including inconclusive results), and a runnable README.

## Completion update checklist

- Verify scope exit criteria; record exact commands, results, and deviations.
- Mark scope/report `Complete (YYYY-MM-DD)` and update dates.
- Move the folder into `archive/` and repair affected links.
- Move its dashboard entry to Completed with date, 1–2 line outcome, and archived spec/report links.
- Update the index/archive list, this plan’s date, and next priority.
- Do not reimplement completed milestones unless explicitly asked.
