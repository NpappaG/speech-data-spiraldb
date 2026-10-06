# M02: Prepare one dataset in two formats

- Status: Complete (2026-10-06)
- Phase: 2 / Data
- Dependencies: M01 reader and audio feasibility checks.
- Blocks: M03 real-data selection and later benchmark provenance.

## Background

Reader APIs are established by M01, but no real subset exists. Both formats must derive from one validated table, with enough provenance to detect stale or mismatched artifacts.

## Objectives

- Stream a reproducible source prefix: 50 development examples, then 1,000 for delivery.
- Preserve source-provided encoded audio and explicit order/schema.
- Write equivalent outputs and a preparation manifest tied to their contents.

## Non-goals

No model training, frontend, hosted services, GPU rental, cloud storage, multi-worker tuning, dashboards, or native Spiral integration. No performance target or requirement that Vortex win. No waveform re-encoding, resampling, data augmentation, or full-split download.

## Product decisions

- Source: `openslr/librispeech_asr`, configuration `clean`, split `train.100`, resolved immutable revision. Disable automatic audio decoding with the API supported by the locked `datasets` version.
- Schema: `row_index` int64 (zero-based source order), `id` string, `speaker_id` int64, `text` string, `duration_s` float64, `word_count` int64, `sample_rate` int32, `num_frames` int64, `audio_bytes` binary; fields are required and non-null.
- Inspect SoundFile headers during preparation: duration = frames / sample rate; word count = `len(text.split())`. Validate mono, 16 kHz, positive frames, unique IDs, and nonempty audio; fail with clip ID on invalid records.
- Write `data/clips.vortex` with the verified default writer and `data/clips.parquet` with Zstandard. Record actual layout/compression settings; equivalent data does not imply identical physical layouts.

## Risks / open questions

The pinned source may expose bytes or a resolvable path. Never trust machine-local paths from source metadata or silently transcode. Streaming can fetch extra shard bytes; bounded example consumption is not a promise of exactly N rows’ network traffic.

## Milestone exit criteria

A repeatable command produces the pinned 1,000-row subset. Both outputs match the canonical table in order, metadata, and original audio bytes. `data/preparation.json` identifies the source, schema, settings, output hashes, row count, file sizes, and preparation time. Offline and opt-in real-data checks pass.

## Beads

### Bead 0: Source and metadata contract

**Why:** Remove ambiguity before building files or downstream filters.

**Scope:**

- [x] 0.1 Add `prepare.py` arguments for revision, positive row limit, and output directory; document defaults, network requirements, and overwrite behavior.
- [x] 0.2 Resolve/persist an immutable source revision; verify config/split and encoded-byte access on a few streaming records. Handle verified accessible paths only when bytes are absent; otherwise fail clearly.
- [x] 0.3 Encode the schema and validation rules above. Test known header-derived durations, whitespace word counts, invalid records, and duplicate IDs using offline fixtures.

**Exit criteria:** A few real records can be consumed without automatic waveform decoding; schema/rule tests pass and the immutable revision is recorded.

### Bead 1: Canonical subset and format publication

**Why:** Make both readers consume precisely the same input.

**Scope:**

- [x] 1.1 Consume the requested prefix in source order; fail if fewer than N records exist. Preserve bytes and assign contiguous row indices; first exercise 50 rows.
- [x] 1.2 Write both formats from the single validated table into staging files. Read each back and compare every logical field and audio payload to the canonical source table.
- [x] 1.3 Publish validated outputs and `data/preparation.json` last, including schema version, ordered IDs/audio hashes, source/settings, package versions, file hashes/sizes, and preparation timing. Reject existing outputs unless overwrite is explicit; invalidate the old manifest before overwriting so partial publication cannot appear valid.

**Exit criteria:** The 50-row pair matches the original table; failed/interrupted preparation cannot pass as a valid pair. No generated data is tracked.

### Bead 2: Reproducibility and delivery subset

**Why:** Verify the real artifact contract before selection work depends on it.

**Scope:**

- [x] 2.1 Add opt-in real-data verification that checks the manifest, both outputs, ordered metadata, and audio hashes. Missing data yields an explicit setup error when opted in, not a passing skip.
- [x] 2.2 Repeat the 50-row preparation at the same revision in a fresh output directory and compare logical rows/audio hashes; do not require byte-identical container files or identical elapsed times.
- [x] 2.3 Prepare and verify the 1,000-row delivery subset; update exact README commands and capture acquisition/codec friction as it occurs.

**Exit criteria:** Repeated prefixes have identical logical contents; the 1,000-row pair and manifest pass real-data verification.
