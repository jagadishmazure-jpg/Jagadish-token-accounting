"""Cost ledger: dollars per request, per customer and per month, at separate input and output prices.

Prices are illustrative defaults ($0.50 per million input tokens, $1.50 per million output tokens),
not a quote from any provider. Decimal arithmetic avoids float drift in totals.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MILLION = Decimal(1_000_000)


@dataclass(frozen=True)
class Prices:
    input_per_million: Decimal = Decimal("0.50")
    output_per_million: Decimal = Decimal("1.50")
    as_of: str = "illustrative, 2026-10"

    def __post_init__(self) -> None:
        for k in ("input_per_million", "output_per_million"):
            v = getattr(self, k)
            if not isinstance(v, Decimal):
                object.__setattr__(self, k, v := Decimal(str(v)))
            if not v.is_finite() or v < 0:
                raise ValueError(f"{k} must be a finite, non-negative number")

    def cost(self, tokens_in: int, tokens_out: int) -> Decimal:
        for k, v in (("tokens_in", tokens_in), ("tokens_out", tokens_out)):
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError(f"{k} must be a non-negative integer")
        return (Decimal(tokens_in) * self.input_per_million + Decimal(tokens_out) * self.output_per_million) / MILLION


@dataclass(frozen=True)
class Entry:
    customer: str
    month: str
    tokens_in: int
    tokens_out: int
    cost: Decimal


class Ledger:
    def __init__(self, prices: Prices | None = None) -> None:
        self.prices = prices or Prices()
        self.entries: list[Entry] = []

    def record(self, customer: str, month: str, tokens_in: int, tokens_out: int) -> Entry:
        if not customer:
            raise ValueError("customer is required")
        if not MONTH.match(month):
            raise ValueError("month must look like YYYY-MM")
        e = Entry(customer, month, tokens_in, tokens_out, self.prices.cost(tokens_in, tokens_out))
        self.entries.append(e)
        return e

    def by_customer(self) -> dict[str, Decimal]:
        out: dict[str, Decimal] = defaultdict(Decimal)
        for e in self.entries:
            out[e.customer] += e.cost
        return dict(out)

    def by_month(self) -> dict[str, Decimal]:
        out: dict[str, Decimal] = defaultdict(Decimal)
        for e in self.entries:
            out[e.month] += e.cost
        return dict(out)

    def by_customer_month(self) -> dict[tuple[str, str], Decimal]:
        out: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for e in self.entries:
            out[(e.customer, e.month)] += e.cost
        return dict(out)

    def total(self) -> Decimal:
        return sum((e.cost for e in self.entries), Decimal(0))

    def split(self) -> dict[str, Decimal]:
        tin = sum(e.tokens_in for e in self.entries)
        tout = sum(e.tokens_out for e in self.entries)
        return {
            "input_cost": Decimal(tin) * self.prices.input_per_million / MILLION,
            "output_cost": Decimal(tout) * self.prices.output_per_million / MILLION,
        }
