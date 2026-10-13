"""Syllable estimation + line-fit heuristics for lyric conditioning."""
from __future__ import annotations

import re

_VOWEL_GROUP = re.compile(r"[aeiouy]+", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z']+")


def count_syllables(word: str) -> int:
    """Estimate syllables in an English word.

    Heuristic: count vowel groups, subtract a silent trailing 'e' when the
    word has more than one group. Returns at least 1 for any alphabetic word.
    """
    clean = re.sub(r"[^A-Za-z']", "", word).lower()
    if not clean:
        return 0
    groups = _VOWEL_GROUP.findall(clean)
    count = len(groups)
    if clean.endswith("e") and not clean.endswith(("le", "ee", "ye")) and count > 1:
        count -= 1
    return max(count, 1)


def line_syllables(line: str) -> int:
    """Total estimated syllables across a lyric line."""
    return sum(count_syllables(w) for w in _WORD.findall(line))


def fits_meter(line: str, target: int, tolerance: int = 2) -> bool:
    """True when the line's syllable count is within ``tolerance`` of target."""
    return abs(line_syllables(line) - target) <= tolerance