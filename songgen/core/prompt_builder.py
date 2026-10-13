"""Composes the vocal + instrumental conditioning prompts from a SongSpec."""
from __future__ import annotations

from songgen.models.song import SongSpec

_STRUCTURE_TAGS = {
    "verse": "[verse]",
    "chorus": "[chorus]",
    "bridge": "[bridge]",
    "intro": "[intro]",
    "outro": "[outro]",
}


def build_vocal_prompt(spec: SongSpec) -> str:
    """Build the text conditioning string fed to the vocal model.

    Format: genre tags, then mood tags, then a key/bpm bracket, then the
    structured lyric block. The vocal model was trained on this exact layout;
    reordering it degrades intelligibility measurably (~15% WER at v3).
    """
    tags = ", ".join(spec.genre_tags + spec.mood_tags)
    header = f"{tags} | {spec.key} | {spec.bpm}bpm | vocal={spec.vocal_style}"
    body = "\n".join(
        f"{_STRUCTURE_TAGS.get(sec.kind, '[verse]')} {sec.text}" for sec in spec.sections
    )
    return f"{header}\n{body}"


def build_instrumental_prompt(spec: SongSpec) -> str:
    """Build the text conditioning string fed to the instrumental model."""
    tags = ", ".join(spec.genre_tags + spec.instrument_tags)
    return f"{tags} | {spec.key} | {spec.bpm}bpm | {spec.duration_seconds}s | no_vocals"