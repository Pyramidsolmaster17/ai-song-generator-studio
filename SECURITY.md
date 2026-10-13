# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.6.x   | :white_check_mark: |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

`ai-song-generator-studio` renders user-supplied lyrics through a local LLM
front-end and pipes generated audio through `ffmpeg`. The attack surface we
care most about:

- **Prompt-injection via lyrics** — a user-supplied lyric block that tries to
  eject the vocal-model conditioning prompt. Report to `security@ai-song-generator-studio.dev`.
- **Arbitrary file write via output template** — the `--out` flag accepts a
  template string. Path traversal is blocked in `services/render_service.py`
  but we want any bypass reported.
- **Model deserialization** — `.ckpt` / `.safetensors` files are loaded with
  `weights_only=True` where the backend supports it. Legacy `.bin` torch
  pickle files are **not** loaded by default.
- **ffmpeg shell injection** — we never shell out; we use `subprocess.run`
  with an argv list. If you find a path where a user-controlled string reaches
  a shell, that's a critical.

Do **not** open a public issue for security reports. Email the address above.
We aim to acknowledge within 72 hours and ship a patch within 14 days for
confirmed issues.

## Out of scope

- Generated-song content moderation. This is a creative tool; the operator is
  responsible for what they render.
- Copyright claims on rendered output. That's a legal matter, not a security
  one.