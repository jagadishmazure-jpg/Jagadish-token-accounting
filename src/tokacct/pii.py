"""Mask PII before anything reaches a log line or an error message."""

from __future__ import annotations

import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
PHONE = re.compile(r"(?<![\w(])(?:\+?\d{1,2}[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}\b")


def luhn_ok(digits: str) -> bool:
    d = [int(c) for c in digits if c.isdigit()]
    if not 13 <= len(d) <= 19:
        return False
    total = 0
    for i, x in enumerate(reversed(d)):
        if i % 2:
            x *= 2
            if x > 9:
                x -= 9
        total += x
    return total % 10 == 0


def redact(text: str) -> str:
    text = EMAIL.sub("[EMAIL]", text)
    text = SSN.sub("[SSN]", text)
    text = CARD.sub(lambda m: "[CARD]" if luhn_ok(m.group()) else m.group(), text)
    return PHONE.sub("[PHONE]", text)


def contains_pii(text: str) -> bool:
    return redact(text) != text
