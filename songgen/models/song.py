"""Core song data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SectionKind(str, Enum):
    INTRO = "intro"
    VERSE = "verse"
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"


@dataclass(frozen=True)
class LyricSection:
    kind: SectionKind
    text: str


@dataclass(frozen=True)
class SongSpec:
    """Everything needed to render one song.

    Attributes:
        title: Human-readable title, used in the output filename.
        prompt: Free-text seed prompt from the user.
        genre_tags: e.g. ("synthwave", "dream pop").
        mood_tags: e.g. ("melancholic", "euphoric").
        instrument_tags: e.g. ("analog pads", "gated snare").
        vocal_style: one of "female", "male", "duet", "choir", "instrumental".
        key: Musical key, e.g. "A minor".
        bpm: Tempo in beats per minute.
        duration_seconds: Target length.
        sections: Ordered lyric sections.
    """

    title: str
    prompt: str
    genre_tags: tuple[str, ...] = ()
    mood_tags: tuple[str, ...] = ()
    instrument_tags: tuple[str, ...] = ()
    vocal_style: str = "female"
    key: str = "A minor"
    bpm: int = 96
    duration_seconds: int = 180
    sections: tuple[LyricSection, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RenderJob:
    spec: SongSpec
    out_path: Path
    seed: int | None = None
    loudness_lufs: float = -14.0


@dataclass(frozen=True)
class RenderResult:
    out_path: Path
    duration_seconds: float
    vocal_stem: Path | None
    instrumental_stem: Path | None
    peak_dbfs: float
    warnings: tuple[str, ...] = ()