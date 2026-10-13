"""Entry/bootstrap. Wires services together and hands off to a handler."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from songgen.config.settings import load_settings
from songgen.handlers.cli_handler import CliHandler
from songgen.services.lyric_service import LyricService
from songgen.services.render_service import RenderService
from songgen.services.vocal_service import VocalService
from songgen.adapters.ffmpeg_adapter import FfmpegAdapter
from songgen.adapters.model_adapter import ModelAdapter


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_container(settings) -> CliHandler:
    model = ModelAdapter(
        vocal_ckpt=settings.paths.vocal_ckpt,
        instrumental_ckpt=settings.paths.instrumental_ckpt,
        device=settings.runtime.device,
    )
    ffmpeg = FfmpegAdapter(binary=settings.runtime.ffmpeg_binary)
    lyrics = LyricService(model=model, max_lines=settings.generation.max_lyric_lines)
    vocals = VocalService(model=model, sample_rate=settings.audio.sample_rate)
    render = RenderService(
        model=model,
        ffmpeg=ffmpeg,
        vocals=vocals,
        out_dir=Path(settings.paths.output_dir),
    )
    return CliHandler(lyrics=lyrics, vocals=vocals, render=render, settings=settings)


def main(argv: list[str] | None = None) -> int:
    settings = load_settings()
    _configure_logging(settings.runtime.log_level)
    handler = build_container(settings)
    return handler.run(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())