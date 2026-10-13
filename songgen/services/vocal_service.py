"""VocalService — renders the vocal stem from lyric sections."""
from __future__ import annotations

import logging
from pathlib import Path

from songgen.models.backends import VocalRenderRequest
from songgen.models.song import SongSpec

log = logging.getLogger(__name__)


class VocalService:
    """Drives the vocal model and writes the vocal stem to disk."""

    def __init__(self, model, sample_rate: int = 44100) -> None:
        self._model = model
        self._sample_rate = sample_rate

    def render_stem(self, spec: SongSpec, out_path: Path, seed: int | None = None) -> Path:
        """Render the vocal stem for ``spec`` to ``out_path``.

        Returns the path written. Raises ``RuntimeError`` if the model produces
        zero frames (usually a bad conditioning prompt or an OOM).
        """
        lyrics = "\n".join(f"[{s.kind.value}] {s.text}" for s in spec.sections if s.text.strip())
        if not lyrics:
            raise RuntimeError("no lyric text to render; run LyricService.generate first")

        req = VocalRenderRequest(
            prompt=spec.prompt,
            lyrics=lyrics,
            seed=seed,
            out_path=out_path,
        )
        frames = self._model.render_vocals(req)
        if frames is None or len(frames) == 0:
            raise RuntimeError("vocal model returned zero frames")
        self._model.write_audio(frames, out_path, sample_rate=self._sample_rate)
        log.info("vocal stem written: %s (%d frames)", out_path, len(frames))
        return out_path

    @property
    def sample_rate(self) -> int:
        return self._sample_rate