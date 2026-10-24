import pytest

from tokacct.gateway import Gateway, GatewayConfig, mask_id
from tokacct.ratelimit import RequestRateLimiter
from tokacct.request import Request
from tokacct.scenarios import scenarios

SC = scenarios()


def gw(count, budget=10_000, **cfg):
    return Gateway(count, {"Harbor Lane Clinic": budget}, GatewayConfig(**cfg))


C = "Harbor Lane Clinic"


def test_allows_short_chat(o200k):
    d = gw(o200k).check(C, SC["short_chat"], now=0)
    assert d.allowed and d.input_tokens > 0 and d.reserved_output == 1024


def test_unknown_customer(o200k):
    assert gw(o200k).check("someone else", SC["short_chat"], 0).reason == "unknown_customer"


@pytest.mark.parametrize("bad", [0, -5])
def test_invalid_max_output(o200k, bad):
    assert gw(o200k).check(C, SC["short_chat"], 0, max_output=bad).reason == "invalid_max_output"


def test_rate_limit_101st_request(words_count):
    g = gw(words_count, budget=10**9)
    outs = [g.check(C, Request("s", "u"), now=0.5).reason for _ in range(101)]
    assert outs.count("ok") == 100 and outs[-1] == "rate_limited"


def test_rate_window_slides(words_count):
    g = gw(words_count, budget=10**9)
    for _ in range(100):
        g.check(C, Request("s", "u"), now=0.0)
    assert g.check(C, Request("s", "u"), now=1.0).allowed


def big(n_hist=10, n_docs=3):
    hist = [("user" if i % 2 == 0 else "assistant", "word " * 300) for i in range(n_hist)]
    return Request("system", "question", history=hist, docs=["doc " * 300] * n_docs)


def test_reject_mode_rejects_over_cap(words_count):
    d = gw(words_count, budget=10**9, input_cap=1000, mode="reject").check(C, big(), 0)
    assert not d.allowed and d.reason == "input_over_cap" and d.input_tokens > 1000


def test_trim_mode_drops_oldest_history_first(words_count):
    d = gw(words_count, budget=10**9, input_cap=2500).check(C, big(), 0)
    assert d.allowed and d.input_tokens <= 2500
    assert d.trimmed and set(d.trimmed) == {"history_turn"}
    assert d.request.history[-1] == big().history[-1]


def test_trim_falls_back_to_docs(words_count):
    d = gw(words_count, budget=10**9, input_cap=500).check(C, big(), 0)
    assert d.allowed and "doc" in d.trimmed and not d.request.history


def test_trim_does_not_mutate_original(words_count):
    r = big()
    gw(words_count, budget=10**9, input_cap=500).check(C, r, 0)
    assert len(r.history) == 10 and len(r.docs) == 3


def test_trim_cannot_fix_huge_user_text(words_count):
    d = gw(words_count, budget=10**9, input_cap=100).check(C, Request("s", "x " * 500), 0)
    assert d.reason == "input_over_cap_after_trim"


def test_output_reserve_capped_by_context(words_count):
    g = gw(words_count, budget=10**9, input_cap=1000, context_window=1100, min_output=50)
    d = g.check(C, Request("s", "x " * 990), 0, max_output=500)
    assert d.allowed and d.input_tokens + d.reserved_output == 1100


def test_reserve_never_below_min_output_at_cap(words_count):
    g = gw(words_count, budget=10**9, input_cap=1000, context_window=1064, min_output=64)
    d = g.check(C, Request("s", "x " * 990), 0)
    assert d.allowed and d.reserved_output >= 64


def test_budget_exceeded(words_count):
    g = gw(words_count, budget=100)
    assert g.check(C, Request("s", "u"), 0, max_output=50).allowed
    assert g.check(C, Request("s", "u"), 0, max_output=50).reason == "token_budget_exceeded"


def test_budget_charges_input_plus_reserve(words_count):
    g = gw(words_count)
    d = g.check(C, Request("s", "u"), 0, max_output=100)
    assert g.used[C] == d.input_tokens + 100


def test_settle_releases_unused(words_count):
    g = gw(words_count)
    d = g.check(C, Request("s", "u"), 0, max_output=100)
    assert g.settle(d.reservation_id, 30) == 70
    assert g.used[C] == d.input_tokens + 30


def test_settle_twice_fails(words_count):
    g = gw(words_count)
    d = g.check(C, Request("s", "u"), 0, max_output=100)
    g.settle(d.reservation_id, 1)
    with pytest.raises(KeyError):
        g.settle(d.reservation_id, 1)


@pytest.mark.parametrize("out", [-1, 101])
def test_settle_bad_output(words_count, out):
    g = gw(words_count)
    d = g.check(C, Request("s", "u"), 0, max_output=100)
    with pytest.raises(ValueError):
        g.settle(d.reservation_id, out)


def test_settled_budget_allows_more(words_count):
    g = gw(words_count, budget=120)
    d = g.check(C, Request("s", "u"), 0, max_output=100)
    g.settle(d.reservation_id, 0)
    assert g.check(C, Request("s", "u"), 0, max_output=100).allowed


def test_negative_budget_rejected(words_count):
    with pytest.raises(ValueError):
        Gateway(words_count, {"x": -1})


@pytest.mark.parametrize(
    "kw",
    [{"input_cap": 0}, {"rps": 0}, {"mode": "drop"}, {"input_cap": 20000, "context_window": 16384}, {"min_output": -1}],
)
def test_bad_config(kw):
    with pytest.raises(ValueError):
        GatewayConfig(**kw)


def test_log_masks_customer_and_hides_text(words_count):
    g = gw(words_count, budget=1)
    secret = "my card 4111 1111 1111 1111 and mail ana@example.com"
    g.check(C, Request("s", secret), 0)
    joined = " ".join(g.log)
    assert C not in joined and "4111" not in joined and "example.com" not in joined
    assert mask_id(C) in joined


def test_reasons_never_echo_text(words_count):
    g = gw(words_count, input_cap=10, mode="reject")
    d = g.check(C, Request("s", "SSN 123-45-6789 " * 20), 0)
    assert "123-45-6789" not in d.reason


def test_mask_id_stable():
    assert mask_id("a") == mask_id("a") != mask_id("b")


def test_limiter_rejects_bad_rps():
    with pytest.raises(ValueError):
        RequestRateLimiter(0)
