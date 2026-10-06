# Developer Experience

## M01: Environment setup (2026-10-06)

- The inherited pyenv Python 3.13.5 and available pyenv Python 3.12.7 emit
  `hashlib` errors for missing BLAKE2 implementations. A healthy Homebrew
  Python 3.11.15 passes the same hashing check. The project selects that
  interpreter explicitly without altering global Python configuration.
- Poetry 1.5.1 is already installed. The project uses `poetry install --no-root`
  because its entry points are repository scripts rather than an installable package.
- macOS 26.6.2 on Apple Silicon arm64 is the initial verification platform.
- Source acquisition will use Hugging Face `datasets`; file reads use Vortex and
  PyArrow directly. This keeps source integration separate from format timing.

Verified versions: Vortex 0.87.0, PyArrow 25.0.1, torch 2.14.1,
datasets 5.1.0, SoundFile 0.13.1, NumPy 2.4.6, pytest 9.1.1.

Both readers support Dataset scanners with native filters/projections,
`batch_size=2` and `use_threads=False` in the feasibility test. Vortex exposes
Arrow string/binary view representations; normalization to the canonical schema
is necessary for logical table comparisons. A cookbook example should show
that conversion explicitly. WAV and FLAC decode to the expected float32 samples.

Sandbox DNS initially prevented dependency downloads; approved network escalation
completed lock/install. No global Python or Poetry configuration was changed.

## M02: Source and preparation

- `datasets` 5.1.0 supports `load_dataset(..., streaming=True, revision=..., token=False)`
  with `cast_column("audio", Audio(decode=False))`. The pinned source returns actual
  encoded bytes alongside a path; there is no need to decode through TorchCodec or
  trust stale source-machine paths. Three source records verified mono 16 kHz FLAC
  headers, including clip `374-180298-0000` (232,480 frames).
- The resolved immutable revision is
  `71cacbfb7e2354c4226d01e70d77d5fca3d04ba1` (`clean` / `train.100`).
- Hub access is public and explicitly unauthenticated. A rate-limit suggestion is
  emitted by the Hub client; no credential is required for this workflow.
- A useful acquisition example should distinguish disabling waveform decoding
  from avoiding all extra shard/network I/O, and preserve encoded bytes directly.
