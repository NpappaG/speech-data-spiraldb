# M02 Progress Report

- Status: Complete (2026-10-06)
- Last updated: 2026-10-06

## Delivery summary

Published and independently verified the pinned 1,000-row dataset pair; repeated 50-row preparations have identical logical contents.

All beads and milestone exit criteria passed. Planning baseline: `97ab8e1`.

## Ops notes

- Migrations: None.
- Env vars / secrets: No credentials added. Generated inputs remain under ignored `data/`.
- Deploy / rollout / rollback: Local cookbook only; no deployment.

## Tests run (exact commands)

- `HF_HOME=data/hf-cache .venv/bin/python /tmp/speech_source_probe.py`: 3 encoded-byte records and 16 kHz mono FLAC headers verified.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest -q`: 16 passed, 1 intentionally opt-in real-data test skipped.
- `HF_HOME=data/hf-cache POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python prepare.py --limit 50 --output-dir data/dev50`: passed.
- `HF_HOME=data/hf-cache POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python prepare.py --limit 50 --output-dir data/repeat50`: passed; preflight and full-table comparison against data/dev50 confirmed identical source, ordered IDs, all metadata, and audio hashes.
- `HF_HOME=data/hf-cache POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python prepare.py`: 1,000 rows published; both formats verified against canonical source.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest --real-data -q`: **17 passed**.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry check` and `git diff --check`: passed.

## Decisions / notes

Source pinned at `71cacbfb7e2354c4226d01e70d77d5fca3d04ba1`, clean/train.100. `Audio(decode=False)` exposes encoded FLAC bytes without TorchCodec. Header-derived duration and whitespace word counts, non-null typed fields, mono/rate/frame validation, unique IDs, and source-order indices are implemented.

Prepared artifacts: Vortex 226,064,756 bytes; Parquet 217,925,013 bytes. This run’s preparation took 16.507 seconds, excluded from future benchmarks. Values are local observations, not general performance claims.

Manifest-last publication is tested with an injected replacement interruption. Existing artifacts require explicit overwrite; old selection/preparation provenance is invalidated before replacement. Both outputs are compared to the original canonical table before publication. All generated inputs/cache/provenance are ignored.

The delivered contract is [scope.md](scope.md). The [planning review](../../design_review.md) records the original design rationale.

## Outstanding / deferred

No outstanding work in this milestone. Deferred project scope remains excluded by the spec.
