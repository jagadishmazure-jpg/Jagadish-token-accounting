import json
from pathlib import Path

import pytest

from tokacct import cli
from tokacct.replay import replay
from tokacct.scenarios import CUSTOMERS, workload

ROOT = Path(__file__).parents[1]
RES = json.loads((ROOT / "results.json").read_text())


def test_workload_deterministic():
    a = [(t, c, m) for t, c, _, m in workload(50)]
    b = [(t, c, m) for t, c, _, m in workload(50)]
    assert a == b


def test_workload_customers_fictional_set():
    assert {c for _, c, _, _ in workload(200)} <= set(CUSTOMERS)


@pytest.fixture(scope="module")
def trim(o200k):
    return replay(o200k, mode="trim")


def test_replay_matches_results(trim):
    assert trim == RES["replay_trim"]


def test_replay_reject_matches_results(o200k):
    assert replay(o200k, mode="reject") == RES["replay_reject"]


def test_rate_limit_triggers(trim):
    assert trim["outcomes"]["rate_limited"] > 0


def test_budgets_trigger(trim):
    assert trim["outcomes"]["token_budget_exceeded"] > 0


def test_usage_within_budget(trim):
    assert all(v <= 150_000 for v in trim["tokens_used"].values())


def test_outcomes_sum(trim):
    assert sum(trim["outcomes"].values()) == trim["requests"]


def test_cost_split_adds_up(trim):
    from decimal import Decimal

    assert abs(Decimal(trim["input_cost_usd"]) + Decimal(trim["output_cost_usd"]) - Decimal(trim["total_cost_usd"])) < Decimal("0.000002")


def test_cli_demo(capsys):
    assert cli.main(["demo"]) == 0
    assert "format_overhead" in capsys.readouterr().out


def test_cli_check_passes():
    assert cli.main(["bench", "--check", str(ROOT / "results.json")]) == 0


def test_cli_check_detects_tamper(tmp_path):
    bad = dict(RES)
    bad["replay_trim"] = {**RES["replay_trim"], "trimmed": -1}
    p = tmp_path / "r.json"
    p.write_text(json.dumps(bad))
    assert cli.main(["bench", "--check", str(p)]) == 1


def test_cli_bench_writes(tmp_path):
    out = tmp_path / "r.json"
    assert cli.main(["bench", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["accounting_tokenizer"] == "o200k_base"
