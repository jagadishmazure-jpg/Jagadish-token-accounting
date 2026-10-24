"""How wrong are the quick rules? 4 characters per token and 1.3 tokens per word."""

from __future__ import annotations

import math

from .corpus import CATEGORIES, SAMPLES
from .tokenizers import Counter


def chars_rule(text: str) -> int:
    return math.ceil(len(text) / 4)


def words_rule(text: str) -> int:
    return math.ceil(len(text.split()) * 1.3)


def signed_error_pct(estimate: int, actual: int) -> float:
    if actual <= 0:
        raise ValueError("actual must be positive")
    return round(100 * (estimate - actual) / actual, 1)


def estimate_errors(counter: Counter) -> dict[str, dict[str, float]]:
    out = {}
    for cat in CATEGORIES:
        actual = sum(counter.count(s) for s in SAMPLES[cat])
        out[cat] = {
            "actual": actual,
            "chars_rule": signed_error_pct(sum(chars_rule(s) for s in SAMPLES[cat]), actual),
            "words_rule": signed_error_pct(sum(words_rule(s) for s in SAMPLES[cat]), actual),
        }
    return out
