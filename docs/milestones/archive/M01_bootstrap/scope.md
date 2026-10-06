# M01: Bootstrap and smoke-test

- Status: Complete (2026-10-06)
- Phase: 1 / Foundation
- Dependencies: Existing Git repository; no implementation prerequisites.
- Blocks: M02; establishes reader APIs and test conventions for M03–M05.

## Background

Only planning documents exist. Discovering dependency or binary-column incompatibilities after preparing real audio would waste effort. Prove both formats locally before downloading the subset.

## Objectives

- Install a locked Python environment on the development machine.
- Round-trip the same typed synthetic records through Vortex and Parquet.
- Verify native filtering, projection, ordering, and incremental scan APIs against independent expected results.

## Non-goals

No model training, frontend, hosted services, GPU rental, cloud storage, multi-worker tuning, dashboards, or native Spiral integration. No performance target or requirement that Vortex win. No empty module scaffolding or speculative framework abstractions.

## Product decisions

- Use Poetry, `vortex-data`, `datasets` for source acquisition, PyArrow, PyTorch, SoundFile, and pytest. Verify compatible Python/package versions before locking them.
- Compare direct Vortex and PyArrow readers. Vortex’s Hugging Face reader integration is optional, not a core dependency or benchmark path.
- Create modules when they gain working behavior; keep deterministic synthetic fixtures separate from opt-in real-data checks.

## Risks / open questions

Supported APIs, Arrow binary/string conversions, threading controls, and local audio-codec support must be verified with the installed versions. Online documentation alone is not proof of compatibility.

## Milestone exit criteria

Locked installation succeeds; offline tests prove both formats preserve the typed fixture and return hand-specified projected/filtered rows in order. Incremental scan and SoundFile byte decoding work. Generated artifacts are ignored and the actual setup/test commands are documented.

## Beads

### Bead 0: Environment and repository guardrails

**Why:** Establish a reproducible, bounded setup before introducing data.

**Scope:**

- [x] 0.1 Select a supported Python version, verify package/platform requirements, and create `pyproject.toml` and `poetry.lock` with the dependencies above.
- [x] 0.2 Ignore `data/`, local environments, caches, and temporary outputs; retain tracked benchmark JSON and documentation. Confirm ignore behavior with `git check-ignore`.
- [x] 0.3 Document exact installation and offline test commands in the README; begin `docs/developer-experience.md` with observed setup friction and versions.

**Exit criteria:** Installation from the lockfile and imports succeed; ignore checks pass; a developer can repeat setup using the README.

### Bead 1: Two-format feasibility test

**Why:** Expose format incompatibilities without downloading LibriSpeech.

**Scope:**

- [x] 1.1 Create deterministic temporary-file fixtures with explicit Arrow types, source-order indices, transcript/metadata fields, and binary audio payloads; write the same table to both formats.
- [x] 1.2 Check each full read against the original fixture, not just against the other reader. Verify native filter + metadata-only projection against manually expected IDs, including exact boundaries.
- [x] 1.3 Verify incremental batch iteration, stable order, native filter/projection arguments, and supported reader thread settings. Record exact working APIs and any limitations in the report.

**Exit criteria:** Both readers preserve logical values/schema and expose a usable projected, filtered batch stream; an incompatible API is an explicit blocker, not a silent full-table fallback.

### Bead 2: Audio feasibility and offline test baseline

**Why:** Catch decoding/setup problems while the fixture is still tiny.

**Scope:**

- [x] 2.1 Generate a tiny known-waveform WAV in memory and verify SoundFile can inspect headers and decode its bytes to mono float32 samples. Verify FLAC support needed for the source.
- [x] 2.2 Keep fixtures network-free and generated in pytest temporary directories. Document that real-data checks will be explicitly opted into after M02.
- [x] 2.3 Run the offline suite and record exact commands, results, package versions, and remaining API questions.

**Exit criteria:** `poetry run pytest` succeeds without network or downloaded data, and byte decoding matches known fixture samples.
