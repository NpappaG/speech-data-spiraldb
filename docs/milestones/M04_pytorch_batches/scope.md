# M04: Produce real PyTorch batches

- Status: Planned
- Phase: 4 / Loading
- Dependencies: M03 lazy filtered record iterators.
- Blocks: M05 correctness-gated measurement.

## Background

Selected records are available lazily. The shared decoder and collator need an explicit contract so equivalence tests can catch incorrect padding, sample interpretation, or ordering.

## Objectives

- Yield deterministic CPU PyTorch batches with known shape, dtype, and padding.
- Decode each selected clip once per iteration and no rejected clip.
- Verify the shared path against known samples as well as cross-format results.

## Non-goals

No model training, frontend, hosted services, GPU rental, cloud storage, multi-worker tuning, dashboards, or native Spiral integration. No performance target or requirement that Vortex win. No resampling, channel mixing, normalization, augmentation, shuffle, or persistent decoded-audio cache.

## Product decisions

- One SoundFile decoder reads encoded bytes as mono float32, validates 16 kHz and frame count against metadata, and reports corrupt/mismatched clips with ID.
- Batch contract: `waveforms` float32 `[B, T_max]`, zero padding; `lengths` int64 `[B]` in samples; `transcripts` and `ids` ordered string lists; `sample_rate` = 16000. CPU only, default batch size 16, positive configurable batch size, no shuffle, single process.
- Empty selection yields zero batches; `drop_last` is false. Collate across storage scan-chunk boundaries, retaining only the current bounded chunk and batch, never the whole decoded subset.

## Risks / open questions

Shared-code bugs survive reader-to-reader comparisons. Scan chunks and training batches differ; reader buffering must be bounded/documented. No waveform-equivalence assertion should accidentally compare only padding or IDs.

## Milestone exit criteria

Known-signal tests pass, both formats yield equivalent complete real-data iterations, padding/lengths/transcripts/order are correct, and rejected audio is never decoded. Error and partial-batch behavior is verified offline.

## Beads

### Bead 0: Decoder and waveform contract

**Why:** Establish a trusted shared conversion before measuring it.

**Scope:**

- [ ] 0.1 Implement byte decoding and metadata validation; reject stereo, inconsistent rates/frame counts, empty/corrupt audio with clip-specific errors.
- [ ] 0.2 Test generated PCM samples with independently known waveform values, rate, and lengths; use explicit documented tolerances only where needed.
- [ ] 0.3 Verify real source FLAC support and expected sample counts without adding another decoder backend.

**Exit criteria:** Known samples decode correctly, real FLAC is supported, and invalid payloads/metadata fail with useful errors.

### Bead 1: Lazy batching and edge cases

**Why:** Deliver the actual PyTorch interface without hiding eager loading.

**Scope:**

- [ ] 1.1 Feed either reader into the same decoder/collator; implement the specified contract and default batch size 16.
- [ ] 1.2 Test 0, 1, 16, and 17 selected clips, unequal waveform lengths, different scanner chunk sizes, zero padding, source order, and invalid batch size.
- [ ] 1.3 Instrument decode calls: each selected ID is decoded once, rejected IDs never are, and the first batch is yielded before all selected clips are decoded. Close reader resources when iteration ends or is stopped early.

**Exit criteria:** Batch output is independent of storage chunking, has a final partial batch, and remains lazy with deterministic decoder counts.

### Bead 2: Full real-data equivalence gate

**Why:** Establish correctness evidence that measurement cannot bypass.

**Scope:**

- [ ] 2.1 Iterate both formats completely, comparing each batch’s IDs, transcripts, lengths, sample rate, shapes, padding, and waveform samples without retaining all batches.
- [ ] 2.2 Verify concatenated membership against M03’s independently checked selection; check total clips and expected batch count.
- [ ] 2.3 Run offline and opt-in real-data tests; document the batch API/example and actual validation commands/results.

**Exit criteria:** Both complete real iterations match the independent membership and shared waveform contract; correctness tests are ready to gate M05.
