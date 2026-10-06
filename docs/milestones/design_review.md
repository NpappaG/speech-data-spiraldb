# Bead Design Review

- Reviewed: 2026-10-06
- Scope: All 12 original beads across M01–M06; revised into 18 independently verifiable beads.
- Outcome: Six-milestone sequence retained. All milestones remain Planned; this review delivers planning documents only.

## Findings and revisions

| Original bead | Gap found | Revised checkpoint |
| --- | --- | --- |
| M01 / 0: Environment | Required a Vortex/Hugging Face integration without a clear role; dependency feasibility lacked evidence. | Lock only the needed direct-reader/source stack; check platform, ignores, and actual setup commands. |
| M01 / 1: Skeleton/smoke | Vortex-only smoke test could miss the Parquet or binary-data path; empty skeletons prove little. | Verify both formats against a typed fixture, then separately verify byte decoding and offline tests. |
| M02 / 0: Streaming | Revision resolution, metadata definitions, sample rate, identity, and invalid records were underspecified. | Establish immutable source access and explicit schema; validate headers, word counts, IDs, and bounded prefix consumption. |
| M02 / 1: Outputs | Reader equality could hide altered source bytes; partially overwritten files could look valid. | Compare each output to the canonical table, publish a content-linked manifest last, and verify repeated source prefixes before the final subset. |
| M03 / 0: Selection | Two correct-looking readers could share predicate bugs; separate selection/audio APIs suggested an unnecessary two-pass benchmark. | Hand-label a boundary oracle, then implement separate metadata scans and fresh lazy filtered audio scans. |
| M03 / 1: Manifest/checks | Membership was not tied to actual files and could become an untimed benchmark shortcut. | Record artifact identity, independently check real membership, and keep manifests out of timed selection. |
| M04 / 0: Decode/batch | No tensor shape/dtype/padding contract; a shared decoder could be wrong in both readers. | Test known waveform samples and invalid audio first, then implement explicit CPU batch semantics. |
| M04 / 1: Equivalence | Final partial batches depended on incidental real membership; eager decoding could pass equality checks. | Test 0/1/16/17 clips and chunk boundaries; count decode calls and verify lazy first yield before full real-data equivalence. |
| M05 / 0: Harness | Timing setup, preloaded state, and sustained-throughput denominator were undefined. | Define fresh-open boundaries, full-consumption counts, end-to-end versus remaining-stream rates, and deterministic timing checks. |
| M05 / 1: Evidence | Cache policy and noisy small-run interpretation lacked a gate. | Correctness first, explicit warm-ups and alternating paired trials, complete raw evidence, then a separate rerun and bounded interpretation. |
| M06 / 0: Docs | Deferring commands/friction notes until the end encourages inaccurate recollection. | Update docs as each milestone ships; consolidate results and review evidence-backed feedback separately. |
| M06 / 1: Acceptance | “Clean checkout” could still rely on untracked code, data, or local setup. | Require a clean tracked revision, fresh project environment, offline tests first, then explicit online acquisition and real-data execution. |

## Architecture and measurement decisions

- **Direct readers:** Hugging Face acquires source records; Vortex and PyArrow scan the prepared files. An additional Hugging Face Vortex reader layer is unnecessary for the baseline and would complicate attribution.
- **Two APIs, not two mandatory passes:** Metadata-only selection is useful independently. Training batches use a fresh filtered audio scan; materializing IDs first is not required. Persisted-index fetching can be explored later.
- **Order and provenance:** Explicit row indices, sample-rate/frame metadata, required field validation, and file/audio hashes make membership and artifact mismatches inspectable. These are preparation/validation costs, not hidden timed scan costs.
- **Logical versus physical work:** Scanner projection excludes audio from metadata results and rejected clips are not waveform-decoded. Neither statement proves that storage reads zero extra pages/bytes; physical-I/O claims require instrumentation.
- **Small experiment, honest conclusions:** Keep 50 development and 1,000 delivery clips. Report variation, ties, and regressions. Larger datasets, multiple selectivities, and I/O counters remain future candidates rather than prerequisites.
- **Evidence without ceremony:** Beads are Markdown work chunks, not a requirement to install a task-tracking service. Three meaningful checkpoints per milestone replace mixed or oversized beads; no new runtime framework is prescribed.

## Primary documentation checked

Checked on 2026-10-06; implementation must confirm these APIs against locked installed versions.

- [Vortex Dataset API](https://docs.vortex.dev/api/python/dataset): native filter/projection and scanner APIs; some scanner settings are unsupported. Use verified controls rather than assuming identical library internals.
- [Vortex I/O API](https://docs.vortex.dev/api/python/io): scans, incremental Arrow-reader access, and writer options. Byte retrieval granularity depends on the format/layout.
- [Hugging Face audio loading](https://huggingface.co/docs/datasets/audio_load): automatic decoding can be disabled; choose the supported API for the pinned version.
- [LibriSpeech dataset card](https://huggingface.co/datasets/openslr/librispeech_asr): source metadata and attribution; verify the selected configuration/split at the pinned revision.
- [PyArrow Scanner](https://arrow.apache.org/docs/python/generated/pyarrow.dataset.Scanner.html): projection, filtering, record-batch iteration, and reader settings.
- [SoundFile documentation](https://python-soundfile.readthedocs.io/en/latest/): file/byte decoding and header information used to specify the preparation and waveform contracts.

## Verification of this revision

Documentation validation passed for 18 Markdown files: relative links, required spec/report sections, 18 bead exits, 54 uniquely numbered tasks, consistent Planned status, and whitespace checks including untracked files. No pipeline, dataset, or benchmark has been executed during this planning review; milestone reports continue to state that implementation tests have not run.
