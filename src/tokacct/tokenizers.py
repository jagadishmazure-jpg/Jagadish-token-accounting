"""One interface over every tokenizer the repo measures."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .bpe import BPETokenizer
from .corpus import BPE_TRAINING_TEXT

BPE_VOCAB = 512
SPM_ENV = "TOKACCT_SPM_MODEL"
DEFAULT_SPM = Path.home() / ".cache" / "tokacct" / "spiece.model"


@dataclass(frozen=True)
class Counter:
    name: str
    count: Callable[[str], int]


@lru_cache(maxsize=1)
def scratch_bpe() -> BPETokenizer:
    return BPETokenizer().train(BPE_TRAINING_TEXT, BPE_VOCAB)


def _tiktoken(name: str) -> Counter | None:
    try:
        import tiktoken
    except ImportError:
        return None
    enc = tiktoken.get_encoding(name)
    return Counter(name, lambda t: len(enc.encode(t, disallowed_special=())))


def spm_path() -> Path | None:
    p = Path(os.environ.get(SPM_ENV, DEFAULT_SPM))
    return p if p.is_file() else None


def _sentencepiece() -> Counter | None:
    path = spm_path()
    if path is None:
        return None
    try:
        import sentencepiece as spm
    except ImportError:
        return None
    sp = spm.SentencePieceProcessor(model_file=str(path))
    return Counter("sentencepiece-unigram-32k", lambda t: len(sp.encode(t)))


def available() -> list[Counter]:
    bpe = scratch_bpe()
    out = [Counter(f"scratch-bpe-{BPE_VOCAB}", lambda t: len(bpe.encode(t)))]
    for c in (_tiktoken("cl100k_base"), _tiktoken("o200k_base"), _sentencepiece()):
        if c is not None:
            out.append(c)
    return out


def by_name(name: str) -> Counter:
    for c in available():
        if c.name == name:
            return c
    raise KeyError(f"tokenizer not available: {name}")


def spm_unknown_share(texts: list[str]) -> float | None:
    """Share of SentencePiece pieces that are the unknown id (characters missing from its vocabulary)."""
    path = spm_path()
    if path is None:
        return None
    import sentencepiece as spm

    sp = spm.SentencePieceProcessor(model_file=str(path))
    ids = [i for t in texts for i in sp.encode(t)]
    return round(100 * sum(i == sp.unk_id() for i in ids) / len(ids), 1) if ids else 0.0
