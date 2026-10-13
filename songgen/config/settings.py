"""Layered settings loader: defaults -> songgen.toml -> env -> CLI overrides."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_data_dir


@dataclass(frozen=True)
class PathSettings:
    model_root: Path
    vocal_ckpt: Path
    instrumental_ckpt: Path
    output_dir: Path
    cache_dir: Path


@dataclass(frozen=True)
class RuntimeSettings:
    device: str = "cpu"
    ffmpeg_binary: str = "ffmpeg"
    log_level: str = "info"
    workers: int = 2


@dataclass(frozen=True)
class AudioSettings:
    sample_rate: int = 44100
    channels: int = 2
    bit_depth: int = 16
    loudness_lufs: float = -14.0


@dataclass(frozen=True)
class GenerationSettings:
    max_lyric_lines: int = 48
    default_bpm: int = 96
    default_key: str = "A minor"
    max_song_seconds: int = 300
    seed: int | None = None


@dataclass(frozen=True)
class Settings:
    paths: PathSettings
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    generation: GenerationSettings = field(default_factory=GenerationSettings)


def _default_paths() -> PathSettings:
    root = Path(user_data_dir("ai-song-generator-studio", "songgen"))
    model_root = root / "models"
    return PathSettings(
        model_root=model_root,
        vocal_ckpt=model_root / "weights" / "vocal_v3.safetensors",
        instrumental_ckpt=model_root / "weights" / "instrumental_v3.safetensors",
        output_dir=root / "outputs",
        cache_dir=root / "cache",
    )


def _read_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_settings(config_path: Path | None = None) -> Settings:
    """Resolve settings from defaults, an optional TOML file, and env vars.

    Env overrides: SONGGEN_DEVICE, SONGGEN_FFMPEG, SONGGEN_LOG_LEVEL,
    SONGGEN_OUTPUT_DIR, SONGGEN_SEED.
    """
    base = _default_paths()
    raw = _read_toml(config_path or Path("songgen.toml"))

    runtime_raw = raw.get("runtime", {})
    runtime = RuntimeSettings(
        device=os.environ.get("SONGGEN_DEVICE", runtime_raw.get("device", "cpu")),
        ffmpeg_binary=os.environ.get("SONGGEN_FFMPEG", runtime_raw.get("ffmpeg_binary", "ffmpeg")),
        log_level=os.environ.get("SONGGEN_LOG_LEVEL", runtime_raw.get("log_level", "info")),
        workers=int(runtime_raw.get("workers", 2)),
    )

    audio_raw = raw.get("audio", {})
    audio = AudioSettings(
        sample_rate=int(audio_raw.get("sample_rate", 44100)),
        channels=int(audio_raw.get("channels", 2)),
        bit_depth=int(audio_raw.get("bit_depth", 16)),
        loudness_lufs=float(audio_raw.get("loudness_lufs", -14.0)),
    )

    gen_raw = raw.get("generation", {})
    seed_env = os.environ.get("SONGGEN_SEED")
    generation = GenerationSettings(
        max_lyric_lines=int(gen_raw.get("max_lyric_lines", 48)),
        default_bpm=int(gen_raw.get("default_bpm", 96)),
        default_key=gen_raw.get("default_key", "A minor"),
        max_song_seconds=int(gen_raw.get("max_song_seconds", 300)),
        seed=int(seed_env) if seed_env else gen_raw.get("seed"),
    )

    out_env = os.environ.get("SONGGEN_OUTPUT_DIR")
    paths = PathSettings(
        model_root=base.model_root,
        vocal_ckpt=base.vocal_ckpt,
        instrumental_ckpt=base.instrumental_ckpt,
        output_dir=Path(out_env) if out_env else base.output_dir,
        cache_dir=base.cache_dir,
    )

    return Settings(paths=paths, runtime=runtime, audio=audio, generation=generation)