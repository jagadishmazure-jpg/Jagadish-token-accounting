"""Trains a tiny SentencePiece model in a temp dir so the adapter is tested without any download."""

import pytest

from tokacct import tokenizers
from tokacct.corpus import BPE_TRAINING_TEXT

spm = pytest.importorskip("sentencepiece")


@pytest.fixture(scope="module")
def model(tmp_path_factory):
    d = tmp_path_factory.mktemp("spm")
    (d / "train.txt").write_text(BPE_TRAINING_TEXT.replace(". ", ".\n"))
    spm.SentencePieceTrainer.train(input=str(d / "train.txt"), model_prefix=str(d / "m"), vocab_size=120, model_type="unigram", minloglevel=2)
    return d / "m.model"


def test_adapter_loads_model(monkeypatch, model):
    monkeypatch.setenv(tokenizers.SPM_ENV, str(model))
    names = [c.name for c in tokenizers.available()]
    assert "sentencepiece-unigram-32k" in names


def test_adapter_counts(monkeypatch, model):
    monkeypatch.setenv(tokenizers.SPM_ENV, str(model))
    c = tokenizers.by_name("sentencepiece-unigram-32k")
    assert 0 < c.count("the team reviewed the plan") <= 26


def test_unknown_share_for_unseen_script(monkeypatch, model):
    monkeypatch.setenv(tokenizers.SPM_ENV, str(model))
    assert tokenizers.spm_unknown_share(["దయచేసి"]) > 0
    assert tokenizers.spm_unknown_share([]) == 0.0
