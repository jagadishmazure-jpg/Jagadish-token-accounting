"""Gateway plus ledger replay over a deterministic workload. Output lengths are simulated (labelled)."""

from __future__ import annotations

import random
from collections import Counter as Tally
from collections.abc import Callable

from .gateway import Gateway, GatewayConfig
from .ledger import Ledger
from .scenarios import CUSTOMERS, workload


def replay(count: Callable[[str], int], n: int = 1200, mode: str = "trim", budget: int = 150_000, seed: int = 7) -> dict:
    gw = Gateway(count, dict.fromkeys(CUSTOMERS, budget), GatewayConfig(mode=mode))
    ledger = Ledger()
    rng = random.Random(seed + 1)
    reasons: Tally[str] = Tally()
    trimmed = 0
    for t, cust, req, max_out in workload(n, seed):
        d = gw.check(cust, req, now=t, max_output=max_out)
        reasons[d.reason] += 1
        if not d.allowed:
            continue
        trimmed += bool(d.trimmed)
        actual_out = rng.randint(20, d.reserved_output)  # simulated output length
        gw.settle(d.reservation_id, actual_out)
        ledger.record(cust, "2026-10", d.input_tokens, actual_out)
    split = ledger.split()
    return {
        "requests": n,
        "mode": mode,
        "outcomes": dict(sorted(reasons.items())),
        "trimmed": trimmed,
        "total_cost_usd": str(round(ledger.total(), 6)),
        "input_cost_usd": str(round(split["input_cost"], 6)),
        "output_cost_usd": str(round(split["output_cost"], 6)),
        "by_customer_usd": {k: str(round(v, 6)) for k, v in sorted(ledger.by_customer().items())},
        "tokens_used": dict(sorted(gw.used.items())),
    }
