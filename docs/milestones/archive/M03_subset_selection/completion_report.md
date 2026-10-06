# M03 Progress Report

- Status: Complete (2026-10-06)
- Last updated: 2026-10-06

## Delivery summary

Verified 178 selected clips (17.8%) against an independent metadata predicate, with native lazy scans and content-linked membership provenance.

All beads and milestone exit criteria passed. Planning baseline: `97ab8e1`.

## Ops notes

- Migrations: None.
- Env vars / secrets: No credentials added. Generated inputs remain under ignored `data/`.
- Deploy / rollout / rollback: Local cookbook only; no deployment.

## Tests run (exact commands)

- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest -q`: 28 passed, 2 intentionally opt-in tests skipped.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python loaders.py`: 178 clips independently verified; selection.json saved.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest --real-data -q`: **30 passed** after disabling Vortex segment caching.
- Offline fixtures cover exact/below/above duration/word boundaries, null inputs, empty, no-match, and all-match cases for each format. A scanner spy confirms native projection/predicate, incremental consumption, and early iterator cleanup.

## Decisions / notes

Readers target 64-row native batches with threads disabled. PyArrow batch/fragment readahead is 0; Vortex segment caching is explicitly disabled using the verified `without_segment_cache=True` open argument. Vortex’s pinned file interface has no close() API; generator finalization closes supported iterators and releases scanner/dataset references.

The metadata-only API excludes audio; the audio-record API starts its own filtered scan without a mandatory metadata pre-pass. Neither uses selection manifest membership for production scanning. Native storage may fetch/decompress extra pages: this work guarantees logical selection, not precise physical-I/O savings.

Selection provenance ties predicate, source, ordered IDs/indices, and package versions to preparation/file hashes. Preflight hashes are explicit and outside future timers.

The delivered contract is [scope.md](scope.md). The [planning review](../../design_review.md) records the original design rationale.

## Outstanding / deferred

No outstanding work in this milestone. Deferred project scope remains excluded by the spec.
