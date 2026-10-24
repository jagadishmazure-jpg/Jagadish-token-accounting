import pytest

from tokacct.bpe import PRETOKENIZE, BPETokenizer, _merge, _pairs
from tokacct.corpus import BPE_TRAINING_TEXT, all_samples

SAMPLES = [s for _, s in all_samples()]


def test_round_trip_every_sample(bpe):
    for text in SAMPLES:
        assert bpe.decode(bpe.encode(text)) == text


def test_round_trip_edge_cases(bpe):
    for text in ["", " ", "a", "\n\n", "ÿ", "🧴", "x" * 500, "  two  spaces  ", "snake_case_name"]:
        assert bpe.decode(bpe.encode(text)) == text


def test_vocab_size(bpe):
    assert bpe.vocab_size == 512


def test_merges_compress_training_text(bpe):
    assert len(bpe.encode(BPE_TRAINING_TEXT)) < len(BPE_TRAINING_TEXT.encode()) / 3


def test_untrained_is_bytes():
    t = BPETokenizer()
    assert t.encode("hé") == list("hé".encode())


def test_vocab_below_256_rejected():
    with pytest.raises(ValueError):
        BPETokenizer().train("abc", 100)


def test_training_stops_when_no_repeats():
    t = BPETokenizer().train("abcdefg", 1000)
    assert t.vocab_size == 256


def test_training_is_deterministic():
    a = BPETokenizer().train(BPE_TRAINING_TEXT, 300)
    b = BPETokenizer().train(BPE_TRAINING_TEXT, 300)
    assert a.merges == b.merges


def test_first_merge_is_most_frequent_pair():
    t = BPETokenizer().train("aaaa aaaa aaaa", 257)
    assert (ord("a"), ord("a")) in t.merges


def test_merge_helper():
    assert _merge([1, 2, 1, 2, 3], (1, 2), 9) == [9, 9, 3]


def test_pairs_helper():
    assert _pairs([1, 2, 1, 2])[(1, 2)] == 2


def test_pretokenizer_keeps_all_text():
    s = "Hello, world! It's 2026-10-24."
    assert "".join(PRETOKENIZE.findall(s)) == s


def test_common_word_is_one_token(bpe):
    assert len(bpe.encode(" the")) == 1


def test_unseen_script_costs_more_than_english(bpe):
    eng = "please write a short summary"
    tel = "దయచేసి చిన్న సారాంశం రాయండి"
    assert len(bpe.encode(tel)) > 2 * len(bpe.encode(eng))
