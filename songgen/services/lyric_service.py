"""LyricService — prompt -> structured lyric sections."""
from __future__ import annotations

import logging
import re

from songgen.core.lyric_syllables import fits_meter, line_syllables
from songgen.core.prompt_builder import build_vocal_prompt
from songgen.models.song import LyricSection, SectionKind, SongSpec

log = logging.getLogger(__name__)

_SECTION_SPLIT = re.compile(r"^\[(intro|verse|chorus|bridge|outro)\]\s*$", re.IGNORECASE)
_DEFAULT_SHAPE: tuple[SectionKind, ...] = (
    SectionKind.INTRO,
    SectionKind.VERSE,
    SectionKind.CHORUS,
    SectionKind.VERSE,
    SectionKind.CHORUS,
    SectionKind.BRIDGE,
    SectionKind.CHORUS,
    SectionKind.OUTRO,
)


class LyricService:
    """Generates and normalizes lyrics for a song spec."""

    def __init__(self, model, max_lines: int = 48) -> None:
        self._model = model
        self._max_lines = max_lines

    def generate(self, spec: SongSpec) -> SongSpec:
        """Fill in ``spec.sections`` with model-generated lyrics.

        If ``spec.sections`` already has text, those sections are preserved
        verbatim and only empty ones get generated. Raises ``ValueError`` if
        the generated lyric block exceeds ``max_lines``.
        """
        if any(sec.text.strip() for sec in spec.sections):
            return self._normalize(spec)

        prompt = build_vocal_prompt(spec)
        raw = self._model.generate_lyrics(prompt=prompt, max_lines=self._max_lines)
        sections = self._parse_sections(raw)
        if not sections:
            log.warning("model returned no parseable sections; falling back to shape")
            sections = self._fallback_shape(spec)
        return self._normalize(
            SongSpec(
                title=spec.title,
                prompt=spec.prompt,
                genre_tags=spec.genre_tags,
                mood_tags=spec.mood_tags,
                instrument_tags=spec.instrument_tags,
                vocal_style=spec.vocal_style,
                key=spec.key,
                bpm=spec.bpm,
                duration_seconds=spec.duration_seconds,
                sections=sections,
            )
        )

    def _parse_sections(self, raw: str) -> tuple[LyricSection, ...]:
        out: list[LyricSection] = []
        current: SectionKind | None = None
        buf: list[str] = []

        def flush() -> None:
            if current is not None and buf:
                out.append(LyricSection(kind=current, text="\n".join(buf).strip()))

        for line in raw.splitlines():
            m = _SECTION_SPLIT.match(line.strip())
            if m:
                flush()
                buf = []
                current = SectionKind(m.group(1).lower())
            elif current is not None:
                buf.append(line.rstrip())
        flush()
        return tuple(out)

    def _fallback_shape(self, spec: SongSpec) -> tuple[LyricSection, ...]:
        return tuple(LyricSection(kind=k, text="") for k in _DEFAULT_SHAPE)

    def _normalize(self, spec: SongSpec) -> SongSpec:
        total = 0
        cleaned: list[LyricSection] = []
        for sec in spec.sections:
            text = "\n".join(ln.strip() for ln in sec.text.splitlines() if ln.strip())
            total += len(text.splitlines())
            cleaned.append(LyricSection(kind=sec.kind, text=text))
        if total > self._max_lines:
            raise ValueError(f"lyric block has {total} lines, max is {self._max_lines}")
        return SongSpec(
            title=spec.title,
            prompt=spec.prompt,
            genre_tags=spec.genre_tags,
            mood_tags=spec.mood_tags,
            instrument_tags=spec.instrument_tags,
            vocal_style=spec.vocal_style,
            key=spec.key,
            bpm=spec.bpm,
            duration_seconds=spec.duration_seconds,
            sections=tuple(cleaned),
        )

    def meter_report(self, spec: SongSpec, target: int = 8) -> list[tuple[str, int, bool]]:
        """Return (line, syllable_count, fits_meter) for each lyric line."""
        report: list[tuple[str, int, bool]] = []
        for sec in spec.sections:
            for line in sec.text.splitlines():
                if line.strip():
                    report.append((line, line_syllables(line), fits_meter(line, target)))
        return report