import pytest

from tokacct.request import PARTS, Request, account, message_overhead, priming_overhead, shares
from tokacct.scenarios import scenarios

SC = scenarios()


@pytest.mark.parametrize("name", list(SC))
def test_accounting_invariants(o200k, name):
    p = account(SC[name], o200k)
    assert sum(p[k] for k in PARTS) == p["total"]
    assert abs(sum(shares(p).values()) - 100) < 0.05
    assert p["total"] > 3 * p["user"]
    assert p["format_overhead"] > 0


def test_message_layout():
    r = Request("sys", "hi", history=[("user", "a"), ("assistant", "b")])
    assert [m["role"] for m in r.messages()] == ["system", "user", "assistant", "user"]


def test_tools_go_into_system_and_docs_into_user():
    r = SC["rag_with_docs"]
    m = r.messages()
    assert "lookup_order" in m[0]["content"] and "[doc 1]" in m[-1]["content"]


def test_no_tools_no_docs_text():
    r = Request("s", "u")
    assert r.tools_text() == "" and r.docs_text() == ""


def test_tools_json_is_compact_and_sorted():
    r = Request("s", "u", tools=[{"b": 1, "a": 2}])
    assert '{"a":2,"b":1}' in r.tools_text()


def test_overhead_with_word_counter(words_count):
    assert message_overhead("user", words_count) == 3
    assert priming_overhead(words_count) == 2


def test_overhead_formula_for_simple_request(words_count):
    p = account(Request("s", "u"), words_count)
    assert p["format_overhead"] == 3 + 3 + 2


def test_shares_reject_zero():
    with pytest.raises(ValueError):
        shares({k: 0 for k in (*PARTS, "total")})


def test_tools_dominate_agent_request(o200k):
    s = shares(account(SC["agent_with_tools"], o200k))
    assert s["tools"] == max(s.values())


def test_short_chat_overhead_share_higher_than_rag(o200k):
    a = shares(account(SC["short_chat"], o200k))["format_overhead"]
    b = shares(account(SC["rag_with_docs"], o200k))["format_overhead"]
    assert a > b
