# Milestone Archive



Move completed milestone folders here with their specs, reports, and supporting artifacts. Add dated links and outcomes here and in the [project dashboard](../project_plan.md). Do not reimplement completed milestones unless explicitly asked.

- M01 – Bootstrap and smoke-test: Complete (2026-10-06) — [scope](M01_bootstrap/scope.md), [report](M01_bootstrap/completion_report.md). Locked the Python 3.11 environment and verified both native scanners plus known-sample WAV/FLAC decoding.

- M02 – Prepare one dataset in two formats: Complete (2026-10-06) — [scope](M02_dataset_preparation/scope.md), [report](M02_dataset_preparation/completion_report.md). Published and independently verified the pinned 1,000-row dataset pair; repeated 50-row preparations have identical logical contents.

- M03 – Select a reproducible training subset: Complete (2026-10-06) — [scope](M03_subset_selection/scope.md), [report](M03_subset_selection/completion_report.md). Verified 178 selected clips (17.8%) against an independent metadata predicate, with native lazy scans and content-linked membership provenance.

- M04 – Produce real PyTorch batches: Complete (2026-10-06) — [scope](M04_pytorch_batches/scope.md), [report](M04_pytorch_batches/completion_report.md). Both readers produce identical complete waveform batches: 178 clips in 12 batches, with correct zero padding and a two-clip final batch.

- M05 – Measure without overstating results: Complete (2026-10-06) — [scope](M05_benchmark/scope.md), [report](M05_benchmark/completion_report.md). Saved two correctness-gated invocations with 20 raw trials each; metadata and remaining-stream differences are inconclusive, while first-batch and total times were lower for Vortex in these runs.
