# M06: Package the cookbook

- Status: Complete (2026-10-06)
- Phase: 6 / Delivery
- Dependencies: M05 saved measurements and interpretation; documentation maintained throughout M01–M05.
- Blocks: Final cookbook delivery and stopping rule.

## Background

Commands and experience notes should already exist from earlier milestones. This milestone assembles them into a usable cookbook and verifies there are no hidden local prerequisites.

## Objectives

- Publish a clear local Vortex cookbook with actual commands, contracts, results, and limits.
- Keep source provenance and data attribution visible.
- Verify both offline tests and the online real-data workflow from a clean checkout.

## Non-goals

No model training, frontend, hosted services, GPU rental, cloud storage, multi-worker tuning, dashboards, or native Spiral integration. No performance target or requirement that Vortex win. No new benchmark scope or retrospective invention of onboarding experience.

## Product decisions

- README distinguishes Vortex’s file/scan APIs from Spiral’s broader platform; this project uses no Spiral API.
- Commands and observed developer friction are maintained as work ships; M06 consolidates and verifies them.
- Tests use generated fixtures by default. Real-data verification and acquisition requirements are explicit, not hidden in `pytest`.

## Risks / open questions

Network access, codec availability, source access, or missing tracked files may break a fresh setup. Generated datasets must remain untracked; committed results need provenance without machine secrets or unnecessary absolute paths.

## Milestone exit criteria

A clean tracked checkout in an isolated environment can install locked dependencies, pass offline tests without data/network, prepare the pinned subset with network access, run real-data checks and benchmarks, and explain results from the README. Exact commands and outcomes are recorded; no production performance or Spiral integration claims are implied.

## Beads

### Bead 0: Cookbook and result presentation

**Why:** Make the full experiment understandable and runnable.

**Scope:**

- [x] 0.1 Consolidate README coverage: problem, pipeline, installation/Python requirements, source revision/license attribution, schema/filter/batch contracts, exact commands, output paths, overwrite behavior, and troubleshooting.
- [x] 0.2 Explain offline versus opt-in real-data tests and network/codec requirements. Document all three usage paths: metadata selection, lazy waveform batches, and measurements.
- [x] 0.3 Present actual saved measurements with variation, dataset size/selectivity, and cache policy; state that this is a small local Vortex cookbook, not a Spiral/GPU/training benchmark.

**Exit criteria:** Every documented result points to saved evidence; commands and output contracts cover a complete workflow without guessing.

### Bead 1: Developer feedback and scope closure

**Why:** Preserve useful integration lessons and avoid endless expansion.

**Scope:**

- [x] 1.1 Review `docs/developer-experience.md` notes captured during implementation; attach versions, observed errors, working fixes, and concrete example/API/doc suggestions.
- [x] 1.2 Confirm downloaded/generated audio is ignored, report provenance is useful, and credentials/local sensitive details are absent from committed artifacts.
- [x] 1.3 Check milestone reports reflect delivered scope and deferred items; preserve the stopping rule: correct batches, saved honest measurements, and runnable documentation.

**Exit criteria:** Feedback is evidence-backed, artifacts are suitable for sharing, and deferred ideas have not silently entered delivery scope.

### Bead 2: Clean-checkout acceptance

**Why:** Prove that the repository, rather than the author’s workstation state, contains the recipe.

**Scope:**

- [x] 2.1 Use a clean checkout containing all intended tracked implementation files and lockfile, with a fresh project environment and no copied `data/`. Record the tested commit and environment/cache conditions; a workspace copy of untracked files is not sufficient.
- [x] 2.2 Run documented install and offline tests first without data/network during the tests; then prepare the pinned 1,000 rows, run opt-in real-data verification, and run the benchmark with acquisition network access explicitly available.
- [x] 2.3 Record exact commands/results; repair failures and rerun affected steps. Apply completion/archive rules only when all acceptance criteria pass.

**Exit criteria:** The clean tracked checkout completes the documented workflow; failures are repaired or remain explicit blockers, never reported as completion.
