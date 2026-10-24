import json
from pathlib import Path

import pytest

from tokacct import tokenizers
from tokacct.compare import chars, compare, words
from tokacct.corpus import CATEGORIES, SAMPLES

RESULTS = json.loads((Path(__file__).parents[1] / "results.json").read_text())


def test_six_categories_five_samples_each():
    assert len(CATEGORIES) == 6
    assert all(len(SAMPLES[c]) == 5 for c in CATEGORIES)


def test_tiktoken_counters_available():
    names = [c.name for c in tokenizers.available()]
    assert "cl100k_base" in names and "o200k_base" in names


def test_by_name_unknown():
    with pytest.raises(KeyError):
        tokenizers.by_name("nope")


@pytest.mark.parametrize("name", ["cl100k_base", "o200k_base"])
@pytest.mark.parametrize("text,expected_max", [("hello", 1), ("hello world", 2)])
def test_tiktoken_known_short_counts(name, text, expected_max):
    assert tokenizers.by_name(name).count(text) <= expected_max


@pytest.mark.parametrize("name", ["cl100k_base", "o200k_base"])
def test_special_token_text_is_counted_as_text(name):
    assert tokenizers.by_name(name).count("<|endoftext|>") > 1


def test_words_and_chars():
    assert words("a b  c") == 3 and chars("abc") == 3


@pytest.fixture(scope="module")
def table():
    return compare([c for c in tokenizers.available() if c.name in ("cl100k_base", "o200k_base")])


def test_o200k_not_worse_than_cl100k_by_much(table):
    for cat in CATEGORIES:
        assert table["o200k_base"][cat]["tokens"] <= table["cl100k_base"][cat]["tokens"] * 1.05


@pytest.mark.parametrize("cat", ["hindi", "telugu"])
def test_o200k_much_better_on_indic(table, cat):
    assert table["o200k_base"][cat]["tokens"] * 2 < table["cl100k_base"][cat]["tokens"]


def test_non_english_costs_more_per_word_than_english(table):
    for cat in ["code", "json", "hindi", "telugu", "emoji"]:
        assert table["cl100k_base"][cat]["tokens_per_word"] > table["cl100k_base"]["english"]["tokens_per_word"]


def test_english_near_rule_of_thumb(table):
    assert 1.0 < table["o200k_base"]["english"]["tokens_per_word"] < 1.4


@pytest.mark.parametrize("name", ["cl100k_base", "o200k_base"])
def test_committed_results_match_live(table, name):
    assert RESULTS["compare"][name] == table[name]


def test_scratch_bpe_worse_than_real_tokenizers():
    r = RESULTS["compare"]
    assert all(r["scratch-bpe-512"][c]["tokens"] > r["o200k_base"][c]["tokens"] for c in CATEGORIES)


def test_spm_missing_returns_none(monkeypatch, tmp_path):
    monkeypatch.setenv(tokenizers.SPM_ENV, str(tmp_path / "missing.model"))
    assert tokenizers.spm_path() is None
    assert tokenizers.spm_unknown_share(["x"]) is None


def test_spm_results_recorded_with_unknown_share():
    unk = RESULTS["spm_unknown_pct"]
    assert unk["english"] == 0.0 and unk["hindi"] > 40
