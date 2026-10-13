"""CliHandler — the CLI surface for ai-song-generator-studio."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from songgen.models.song import LyricSection, RenderJob, SectionKind, SongSpec
from songgen.services.lyric_service import LyricService
from songgen.services.render_service import RenderService
from songgen.services.vocal_service import VocalService

log = logging.getLogger(__name__)
console = Console()


class CliHandler:
    """Parses argv, dispatches to services, prints results. No business logic."""

    def __init__(
        self,
        lyrics: LyricService,
        vocals: VocalService,
        render: RenderService,
        settings,
    ) -> None:
        self._lyrics = lyrics
        self._vocals = vocals
        self._render = render
        self._settings = settings

    def run(self, argv: list[str]) -> int:
        app = typer.Typer(add_completion=False, no_args_is_help=True)

        @app.command("generate")
        def generate(
            prompt: str = typer.Argument(..., help="Seed prompt, e.g. 'rainy neon love song'"),
            title: str = typer.Option("Untitled", "--title", "-t"),
            genre: str = typer.Option("synthwave", "--genre", "-g"),
            vocal: str = typer.Option("female", "--vocal", "-v"),
            bpm: int = typer.Option(96, "--bpm"),
            key: str = typer.Option("A minor", "--key"),
            seconds: int = typer.Option(180, "--seconds"),
            out: Path = typer.Option(Path("song.wav"), "--out", "-o"),
            seed: int | None = typer.Option(None, "--seed"),
            json_out: bool = typer.Option(False, "--json"),
        ) -> None:
            spec = SongSpec(
                title=title,
                prompt=prompt,
                genre_tags=tuple(t.strip() for t in genre.split(",") if t.strip()),
                vocal_style=vocal,
                bpm=bpm,
                key=key,
                duration_seconds=seconds,
            )
            spec = self._lyrics.generate(spec)
            result = self._render.render(RenderJob(spec=spec, out_path=out, seed=seed))
            if json_out:
                console.print_json(
                    json.dumps(
                        {
                            "out_path": str(result.out_path),
                            "duration_seconds": result.duration_seconds,
                            "peak_dbfs": result.peak_dbfs,
                            "warnings": list(result.warnings),
                        }
                    )
                )
            else:
                console.print(f"[green]rendered[/green] {result.out_path}")

        @app.command("lyrics")
        def lyrics_cmd(
            prompt: str = typer.Argument(...),
            genre: str = typer.Option("synthwave", "--genre", "-g"),
            json_out: bool = typer.Option(False, "--json"),
        ) -> None:
            spec = SongSpec(
                title="Draft",
                prompt=prompt,
                genre_tags=tuple(t.strip() for t in genre.split(",") if t.strip()),
            )
            spec = self._lyrics.generate(spec)
            if json_out:
                console.print_json(
                    json.dumps([{"kind": s.kind.value, "text": s.text} for s in spec.sections])
                )
                return
            for sec in spec.sections:
                console.print(f"[bold cyan][{sec.kind.value}][/bold cyan]")
                console.print(sec.text or "[dim](empty)[/dim]")

        @app.command("meter")
        def meter_cmd(
            prompt: str = typer.Argument(...),
            target: int = typer.Option(8, "--target"),
        ) -> None:
            spec = self._lyrics.generate(SongSpec(title="Draft", prompt=prompt))
            table = Table(title="meter report")
            table.add_column("line")
            table.add_column("syllables", justify="right")
            table.add_column("fits", justify="center")
            for line, count, ok in self._lyrics.meter_report(spec, target=target):
                table.add_row(line, str(count), "yes" if ok else "no")
            console.print(table)

        @app.command("info")
        def info_cmd() -> None:
            s = self._settings
            table = Table(title="ai-song-generator-studio")
            table.add_row("version", "0.6.2")
            table.add_row("device", s.runtime.device)
            table.add_row("sample_rate", str(s.audio.sample_rate))
            table.add_row("vocal_ckpt", str(s.paths.vocal_ckpt))
            table.add_row("output_dir", str(s.paths