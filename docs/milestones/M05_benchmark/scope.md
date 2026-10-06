# M05: Measure without overstating results

- Status: Active
- Phase: 5 / Measurement
- Dependencies: M04 passing offline and real-data correctness gates.
- Blocks: M06 actual-results documentation.

## Background

Correct batches do not guarantee valid timings. Tiny local runs can be dominated by setup, OS caching, or decoding. The goal is an honest cookbook measurement, not a general Vortex-versus-Parquet ranking.

## Objectives

- Measure fresh metadata scans and fresh end-to-end batch iterations with explicit boundaries.
- Collect five paired rounds with alternating format order and comparable settings.
- Save raw evidence, medians, variation, and a restrained interpretation.

## Non-goals

No model training, frontend, hosted services, GPU rental, cloud storage, multi-worker tuning, dashboards, or native Spiral integration. No performance target or requirement that Vortex win. No automatic dataset expansion, exhaustive selectivity sweep, profiler suite, cache flushing, or unsupported claims about physical bytes read.

## Product decisions

- Use `time.perf_counter`; finish imports, file/hash validation, correctness checks, and environment discovery outside timing. File open/scanner creation belong inside each timed trial; fresh handles and no retained tables, membership, or decoded buffers.
- Metadata metric: start before opening the file; stop after fully consuming projected selected metadata. Count materialized rows, not only scan setup time.
- Batch metrics: a separate fresh filtered scan, with no metadata pre-pass. Start before opening; first-batch latency ends when the first padded waveform batch is yielded; total time ends when the iterator is exhausted. End-to-end throughput = selected clips / total time. Remaining-stream throughput = clips after the first batch / elapsed time from first yield to exhaustion; use null if no clips remain.
- One untimed warm-up per format for each measured path; then five paired rounds alternating Vortex-first and Parquet-first. Label the policy warm-up performed / OS cache uncontrolled; fresh handles do not mean cold cache.
- Use the same logical projections, predicate, scan batch target of 64 rows, CPU-only waveform batch size 16, no shuffle, and single-process policy. Explicitly record library thread/readahead/mmap settings and unavoidable differences, including actual emitted scan chunk sizes; do not claim identical internals.

## Risks / open questions

A 1,000-row run may be too short for stable conclusions; report variability and inconclusive results instead of increasing scope or requiring a speedup. Warm-up/correctness reads affect cache state. Full payload read counts need separate instrumentation and are not inferred from selected row counts.

## Milestone exit criteria

Correctness gates pass. Five measured samples per format/path exist with positive durations, expected clip counts, consistent boundaries, raw timings, medians/ranges, configuration and provenance in `results/measurements.json`. A second invocation verifies rerunnability; timing values need not match.

## Beads

### Bead 0: Timing contract and bookkeeping checks

**Why:** Prevent hidden preprocessing and misleading denominators.

**Scope:**

- [x] 0.1 Add `benchmark.py` with explicit input/output paths, repetitions, and common settings; implement the timing boundaries and metrics above.
- [x] 0.2 Ensure each trial opens a fresh reader and consumes its entire stream; neither manifest membership nor metadata results feed timed audio scans. Exclude JSON writes and heavy correctness comparisons from timing; retain cheap count checks.
- [x] 0.3 Test metric arithmetic and trial ordering using a controlled clock/known iterator; test one-batch, empty-selection rejection, zero/nonpositive timing rejection, and incorrect output counts.

**Exit criteria:** Deterministic checks establish timing boundaries, denominators, first-batch handling, and exactly five samples per format at the default setting.

### Bead 1: Correctness-gated paired execution

**Why:** Collect a bounded, fair comparison of the implemented readers.

**Scope:**

- [ ] 1.1 Run the offline/real-data gates and validate input hashes before timing; abort on failure. Record warm-up policy and perform one warm-up per format/path.
- [ ] 1.2 Run five paired rounds for metadata and five for waveform iteration, alternating format order within each path. Record round/order/counts and release reader resources between trials.
- [ ] 1.3 Persist raw per-trial metrics, medians and min/max, hardware/OS, Python/package/code version, file hashes/sizes, selected fraction, and actual scan/thread/batch/cache settings. Record dirty-worktree state when applicable.

**Exit criteria:** Results contain all measured samples and provenance; paired settings/counts match and no correctness or runtime failure is swallowed.

### Bead 2: Rerun and bounded interpretation

**Why:** Demonstrate repeatability without pretending tiny measurements establish universal performance.

**Scope:**

- [ ] 2.1 Repeat the documented benchmark invocation into a separate result file; verify schema, counts, and metric validity, not equality of timing numbers.
- [ ] 2.2 Compare selection latency, first-batch latency, total throughput, remaining-stream throughput, and variation separately. A difference smaller than observed variation is inconclusive.
- [ ] 2.3 Explain that encoded-audio decoding is shared, file-layout defaults differ, and this local 1,000-row workload cannot establish production/GPU performance. Record ties/regressions; park larger-scale/selectivity/I/O experiments for later.

**Exit criteria:** The harness reruns successfully and the report supports only conclusions warranted by the saved evidence.
