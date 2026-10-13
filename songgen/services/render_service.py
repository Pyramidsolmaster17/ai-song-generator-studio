"""RenderService — orchestrates full-song rendering end to end."""
from __future__ import annotations

import logging
from pathlib import Path

from songgen.core.prompt_builder import build_instrumental_prompt
from songgen.models.backends import InstrumentalRenderRequest
from songgen.models.song import RenderJob, RenderResult
from songgen.services.vocal_service import VocalService

log = logging.getLogger(__name__)


class RenderService:
    """Renders instrumental + vocal stems, mixes them, and normalizes loudness."""

    def __init__(self, model, ffmpeg, vocals: VocalService, out_dir: Path) -> None:
        self._model = model
        self._ffmpeg = ffmpeg
        self._vocals = vocals
        self._out_dir = out_dir

    def render(self, job: RenderJob) -> RenderResult:
        """Render one song per ``job``. Returns a RenderResult with stem paths.

        Side effects: writes ``<title>.wav``, ``<title>.vocal.wav`` and
        ``<title>.instrumental.wav`` under ``self._out_dir``. Raises
        ``FileNotFoundError`` if ffmpeg is missing.
        """
        self._out_dir.mkdir(parents=True, exist_ok=True)
        slug = _slugify(job.spec.title)
        vocal_path = self._out_dir / f"{slug}.vocal.wav"
        inst_path = self._out_dir / f"{slug}.instrumental.wav"
        final_path = job.out_path if job.out_path.is_absolute() else self._out_dir / job.out_path

        inst_req = InstrumentalRenderRequest(
            prompt=build_instrumental_prompt(job.spec),
            duration_seconds=job.spec.duration_seconds,
            seed=job.seed,
            out_path=inst_path,
        )
        self._model.render_instrumental(inst_req)

        self._vocals.render_stem(job.spec, vocal_path, seed=job.seed)

        self._ffmpeg.mix(
            instrumental=inst_path,
            vocal=vocal_path,
            out=final_path,
            loudness_lufs=job.loudness_lufs,
        )

        peak = self._ffmpeg.peak_dbfs(final_path)
        warnings: list[str] = []
        if peak > -0.3:
            warnings.append(f"peak {peak:.2f} dBFS is close to clipping")

        return RenderResult(
            out_path=final_path,
            duration_seconds=float(job.spec.duration_seconds),
            vocal_stem=vocal_path,
            instrumental_stem=inst_path,
            peak_dbfs=peak,
            warnings=tuple(warnings),
        )


def _slugify(title: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in title]
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "untitled"