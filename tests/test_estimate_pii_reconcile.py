import json
from pathlib import Path

import pytest

from tokacct import reconcile
from tokacct.estimate import chars_rule, estimate_errors, signed_error_pct, words_rule
from tokacct.pii import contains_pii, luhn_ok, redact
from tokacct.tokenizers import by_name

ROOT = Path(__file__).parents[1]


def test_rules():
    for text, c, w in [("abcd", 1, 2), ("abcde", 2, 2), ("one two three", 4, 4), ("", 0, 0)]:
        assert chars_rule(text) == c and words_rule(text) == w


def test_signed_error():
    for est, act, exp in [(110, 100, 10.0), (50, 100, -50.0), (100, 100, 0.0)]:
        assert signed_error_pct(est, act) == exp


def test_signed_error_rejects_zero():
    with pytest.raises(ValueError):
        signed_error_pct(1, 0)


def test_estimate_errors_match_results():
    res = json.loads((ROOT / "results.json").read_text())
    assert estimate_errors(by_name("o200k_base")) == res["estimate_error_pct"]["o200k_base"]


def test_rules_overestimate_english_underestimate_json():
    e = estimate_errors(by_name("o200k_base"))
    assert e["english"]["chars_rule"] > 0 and e["json"]["chars_rule"] < 0 and e["json"]["words_rule"] < -50


@pytest.mark.parametrize(
    "text,tag",
    [
        ("mail ana.lee@example.org now", "[EMAIL]"),
        ("ssn 123-45-6789", "[SSN]"),
        ("card 4111 1111 1111 1111", "[CARD]"),
        ("card 4111-1111-1111-1111", "[CARD]"),
        ("call (555) 010-2030", "[PHONE]"),
        ("call +1 555 010 2030", "[PHONE]"),
    ],
)
def test_redact(text, tag):
    assert tag in redact(text) and contains_pii(text)


def test_non_luhn_number_kept():
    assert "[CARD]" not in redact("ref 1234 5678 9012 3456")


def test_luhn():
    assert luhn_ok("4111111111111111") and not luhn_ok("4111111111111112") and not luhn_ok("123")


def test_clean_text_untouched():
    assert not contains_pii("order ORD-20931 shipped")


def test_drift():
    for p, r, exp in [(100, 100, 0.0), (97, 100, -3.0), (105, 100, 5.0)]:
        assert reconcile.drift_pct(p, r) == exp


def test_drift_rejects_zero():
    with pytest.raises(ValueError):
        reconcile.drift_pct(1, 0)


def test_missing_model_raises(monkeypatch, tmp_path):
    monkeypatch.setenv(reconcile.MODEL_ENV, str(tmp_path / "none.gguf"))
    with pytest.raises(FileNotFoundError):
        reconcile.run_local({}, {})


def test_recorded_local_run_own_tokenizer_exact():
    loc = json.loads((ROOT / "results_local_model.json").read_text())
    for row in loc["rows"].values():
        assert row["by_counter"]["model-own-tokenizer"]["prompt_drift_pct"] == 0.0
        assert row["naive_model_tokenizer"]["user_text_only"]["prompt_drift_pct"] < -80


def test_recorded_local_run_cross_tokenizer_drift_small():
    loc = json.loads((ROOT / "results_local_model.json").read_text())
    for row in loc["rows"].values():
        for c in ("cl100k_base", "o200k_base"):
            assert abs(row["by_counter"][c]["prompt_drift_pct"]) < 5
