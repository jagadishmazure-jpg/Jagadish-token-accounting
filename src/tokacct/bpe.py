"""Byte-level BPE written from scratch (no tokenizer libraries).

Training: split text into chunks with a pre-tokenizer regex, turn each chunk into bytes, then
repeatedly merge the most frequent adjacent pair into a new id. Encoding replays the merges in the
order they were learned. Decoding concatenates the bytes of each id. Every byte has its own id, so
any input round-trips, including scripts and emoji never seen in training.
"""

from __future__ import annotations

import re
from collections import Counter

PRETOKENIZE = re.compile(r"'(?:s|t|re|ve|m|ll|d)| ?[^\W\d_]+| ?\d{1,3}| ?(?:[^\s\w]|_)+|\s+(?!\S)|\s+")


def _pairs(ids: list[int]) -> Counter[tuple[int, int]]:
    return Counter(zip(ids, ids[1:], strict=False))


def _merge(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    out, i = [], 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


class BPETokenizer:
    def __init__(self) -> None:
        self.merges: dict[tuple[int, int], int] = {}
        self.vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def train(self, text: str, vocab_size: int) -> BPETokenizer:
        if vocab_size < 256:
            raise ValueError("vocab_size must be at least 256 (one id per byte)")
        chunks = Counter(PRETOKENIZE.findall(text))
        words = {c: list(c.encode("utf-8")) for c in chunks}
        for new_id in range(256, vocab_size):
            stats: Counter[tuple[int, int]] = Counter()
            for c, ids in words.items():
                for p, n in _pairs(ids).items():
                    stats[p] += n * chunks[c]
            if not stats:
                break
            best = max(stats, key=lambda p: (stats[p], -p[0], -p[1]))
            if stats[best] < 2:
                break
            self.merges[best] = new_id
            self.vocab[new_id] = self.vocab[best[0]] + self.vocab[best[1]]
            words = {c: _merge(ids, best, new_id) for c, ids in words.items()}
        return self

    def _encode_chunk(self, chunk: str) -> list[int]:
        ids = list(chunk.encode("utf-8"))
        while len(ids) >= 2:
            pair = min(_pairs(ids), key=lambda p: self.merges.get(p, 1 << 30))
            if pair not in self.merges:
                break
            ids = _merge(ids, pair, self.merges[pair])
        return ids

    def encode(self, text: str) -> list[int]:
        out: list[int] = []
        for chunk in PRETOKENIZE.findall(text):
            out.extend(self._encode_chunk(chunk))
        return out

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.vocab[i] for i in ids).decode("utf-8", errors="replace")
