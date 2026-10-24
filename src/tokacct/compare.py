"""Tokens per word and per character, by content type and tokenizer."""

from __future__ import annotations

from .corpus import CATEGORIES, SAMPLES
from .tokenizers import Counter


def words(text: str) -> int:
    return len(text.split())


def chars(text: str) -> int:
    return len(text)


def compare(counters: list[Counter]) -> dict[str, dict[str, dict[str, float]]]:
    out: dict[str, dict[str, dict[str, float]]] = {}
    for c in counters:
        out[c.name] = {}
        for cat in CATEGORIES:
            texts = SAMPLES[cat]
            t = sum(c.count(s) for s in texts)
            w = sum(words(s) for s in texts)
            ch = sum(chars(s) for s in texts)
            out[c.name][cat] = {
                "tokens": t,
                "words": w,
                "chars": ch,
                "tokens_per_word": round(t / w, 3),
                "tokens_per_char": round(t / ch, 3),
            }
    return out
