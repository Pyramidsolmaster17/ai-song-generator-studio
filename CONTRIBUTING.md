# Contributing to ai-song-generator-studio

Thanks for wanting to make the tater sing. This repo is a service-oriented
Python desktop tool that generates full songs — vocals, lyrics, and
instrumental bed — from a short text prompt.

## Dev setup

```bash
git clone https://github.com/yourname/ai-song-generator-studio.git
cd ai-song-generator-studio
python -m venv .venv
. .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
python -m songgen.bootstrap
```

First run will download the default vocal + instrumental checkpoints into
`models/weights/`. They are gitignored. Do not commit weights.

## Architecture

We follow a service-oriented layout:

- `songgen/handlers/` — thin adapters (CLI, HTTP, GUI). No business logic.
- `songgen/services/` — business logic. One service per concern.
- `songgen/models/` — data models (dataclasses / pydantic).
- `songgen/adapters/` — platform glue (ffmpeg, ONNX runtime, torch).
- `songgen/core/` — pure domain primitives with no I/O.

If you add a feature, the rule is: handler parses, service decides, adapter
talks to the outside world, core stays pure.

## Style

- `ruff` for lint, `black` for format, `mypy --strict` on `songgen/core` and
  `songgen/services`.
- Line length 100.
- No bare `except:`.
- Every public service method gets a docstring with Args/Returns/Raises.

## Tests

```bash
pytest -q
pytest --cov=songgen --cov-report=term-missing
```

Add a test for every new service method. Adapters get integration tests
marked `@pytest.mark.integration` and are skipped when `ffmpeg` is missing.

## Pull requests

- One feature per PR.
- Include a short "why" in the description.
- If you touch the vocal conditioning path, include a rendered sample in the
  PR description (a 10-second clip is fine).

## Commit style

Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`.