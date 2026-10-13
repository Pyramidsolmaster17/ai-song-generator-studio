"""Backend capability + request/response models."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Backend(str, Enum):
    TORCH = "torch"
    ONNX = "onnx"
    DUMMY = "dummy"


@dataclass(frozen=True)
class BackendCapabilities:
    backend: Backend
    device: str
    supports_streaming: bool
    max_seconds: int
    sample_rate: int


@dataclass(frozen=True)
class VocalRenderRequest:
    prompt: str
    lyrics: str
    seed: int | None
    out_path: Path


@dataclass(frozen=True)
class InstrumentalRenderRequest:
    prompt: str
    duration_seconds: int
    seed: int | None
    out_path: Path