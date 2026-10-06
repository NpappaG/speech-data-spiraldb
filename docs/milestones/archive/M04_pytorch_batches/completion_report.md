# M04 Progress Report

- Status: Complete (2026-10-06)
- Last updated: 2026-10-06

## Delivery summary

Both readers produce identical complete waveform batches: 178 clips in 12 batches, with correct zero padding and a two-clip final batch.

All beads and milestone exit criteria passed. Planning baseline: `97ab8e1`.

## Ops notes

- Migrations: None.
- Env vars / secrets: No credentials added. Generated inputs remain under ignored `data/`.
- Deploy / rollout / rollback: Local cookbook only; no deployment.

## Tests run (exact commands)

- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest -q`: 48 passed, 3 intentionally opt-in tests skipped.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run python loaders.py --verify-batches`: complete equality verified, 178 clips / 12 batches.
- `POETRY_CACHE_DIR=/tmp/speech-poetry-cache poetry run pytest --real-data -q`: **51 passed**.
- Tests verify independent known PCM values, corrupt/empty/stereo/rate/frame failures, 0/1/16/17 clips, padding/transcripts/lengths/dtypes, scan chunk sizes 1/3/64 for both formats, decode call counts, and early cleanup.

## Decisions / notes

The shared SoundFile decoder reads float32 mono bytes, validates 16 kHz and frame count, and reports errors with clip ID. The shared CPU collator returns waveforms [B,T_max], int64 sample lengths, ordered transcripts/IDs, and sample_rate=16000. No resampling, augmentation, normalization, or shuffle.

Tests prove the first batch does not decode the entire selected subset and a rejected corrupt payload never reaches decoding. Cross-format equality alone is not the oracle: known PCM samples and independently checked membership are also required. Full real-data comparison retains only the current pair of waveform batches.

The delivered contract is [scope.md](scope.md). The [planning review](../../design_review.md) records the original design rationale.

## Outstanding / deferred

No outstanding work in this milestone. Deferred project scope remains excluded by the spec.
