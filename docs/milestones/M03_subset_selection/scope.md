# M03: Select a reproducible training subset

- Status: Planned
- Phase: 3 / Selection
- Dependencies: M02 validated files and preparation manifest.
- Blocks: M04 lazy audio batches; M05 scan measurements.

## Background

Files are equivalent, but selection semantics and the audio-read path are unspecified. Matching two readers is insufficient: both could use the wrong predicate or eagerly load all audio.

## Objectives

- Verify each reader against an independent expected ordered subset.
- Expose separate metadata-only selection and lazy filtered audio-record iteration.
- Save a reproducible selection manifest without making it a hidden benchmark cache.

## Non-goals

No model training, frontend, hosted services, GPU rental, cloud storage, multi-worker tuning, dashboards, or native Spiral integration. No performance target or requirement that Vortex win. No persisted row-index fetch optimization or mandatory two-pass audio lookup.

## Product decisions

- Predicate: inclusive `3 <= duration_s <= 10` AND `word_count >= 5`; reject null predicate inputs in fixtures. Production records already reject nulls in M02.
- Implement `loaders.py` with metadata selection and a filtered audio-record iterator. Both push the predicate and explicit projections into the native scanner, using the verified APIs.
- The audio iterator repeats the predicate in a fresh scan and yields source-ordered records incrementally; it does not first collect all IDs, read all payloads, or preload a full table. The metadata-only API is independently usable.
- Native readers may fetch/decompress pages or chunks containing unselected rows. Guarantee that rejected audio is never waveform-decoded; do not claim precise physical I/O savings without measurement.

## Risks / open questions

Order and scanner behavior require runtime verification. If the pinned APIs cannot implement the contract, record the blocker and revise the scope before benchmarking; do not hide eager Python filtering behind the same label.

## Milestone exit criteria

Offline boundary/empty/all-match tests establish independent correctness. Both real readers return the same nonempty ordered subset and selected bytes. Metadata scans omit `audio_bytes`, audio-record scans are incremental, and `data/selection.json` is tied to the preparation artifacts.

## Beads

### Bead 0: Independent selection oracle

**Why:** Detect shared predicate bugs before implementing the adapters.

**Scope:**

- [ ] 0.1 Specify projected fields for metadata and audio records; include row index/ID in both and rate/frame metadata in audio records.
- [ ] 0.2 Build hand-labeled fixtures at, below, and above 3/10 seconds and 5 words, plus null inputs, empty, all-match, and no-match cases.
- [ ] 0.3 Specify stable source order and meaningful empty results; verify expectations with a simple reference predicate independent of the reader expressions.

**Exit criteria:** Expected rows and order are explicit, including boundaries and empty selections; each adapter has an independent oracle.

### Bead 1: Native scanner adapters

**Why:** Exercise the format capabilities rather than a full-table Python workaround.

**Scope:**

- [ ] 1.1 Implement both adapters with native predicate/projection and incremental batch reads; set the verified common reader thread policy and document limitations.
- [ ] 1.2 Test each against the oracle; inspect/instrument scanner arguments to verify metadata projection excludes audio and audio iteration does not materialize the full table before yielding.
- [ ] 1.3 Expose artifact-identity validation as an explicit preflight before use, outside benchmark timers; check source order and selected byte/hash equality. Avoid collecting the entire audio subset for production iteration.

**Exit criteria:** Each adapter independently passes selection tests; real selections and bytes match in source order, with observable native scanner use.

### Bead 2: Selection manifest and real-data gate

**Why:** Preserve exact membership without biasing later timings.

**Scope:**

- [ ] 2.1 Save `data/selection.json` with predicate, source revision, preparation/output hashes, ordered row indices/IDs, selected count, package versions, and schema version. Reject stale manifests when explicitly consumed.
- [ ] 2.2 Verify both real metadata selections against a reference computed from prepared metadata; require a nonempty default selection and record its actual selectivity.
- [ ] 2.3 Document that the manifest is provenance only: fresh benchmark scans must not reuse its precomputed membership or an open/preloaded reader.

**Exit criteria:** The default selection is nonempty, independently checked, and reproducibly recorded without becoming an untimed shortcut.
