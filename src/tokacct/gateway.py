"""Pre-flight gateway: count before calling the model.

Order of checks: request rate (100 RPS) -> input cap (reject, or trim oldest history then last
docs) -> output reservation (always fits: config keeps input_cap + min_output inside the window) -> per-customer token budget.
Budgets are charged with input plus the reserved output; settle() returns the unused part once
the real output length is known. Reasons never include message text, and customer ids are masked.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
from collections.abc import Callable
from dataclasses import dataclass, field

from .ratelimit import RequestRateLimiter
from .request import Request, account


@dataclass(frozen=True)
class GatewayConfig:
    input_cap: int = 8_000
    context_window: int = 16_384
    default_output: int = 1_024
    min_output: int = 64
    rps: int = 100
    mode: str = "trim"  # or "reject"

    def __post_init__(self) -> None:
        for k in ("input_cap", "context_window", "default_output", "min_output", "rps"):
            if getattr(self, k) <= 0:
                raise ValueError(f"{k} must be positive")
        if self.mode not in ("trim", "reject"):
            raise ValueError("mode must be 'trim' or 'reject'")
        if self.input_cap + self.min_output > self.context_window:
            raise ValueError("input_cap plus min_output must fit in the context window")


@dataclass
class Decision:
    allowed: bool
    reason: str
    input_tokens: int = 0
    reserved_output: int = 0
    trimmed: list[str] = field(default_factory=list)
    reservation_id: int | None = None
    request: Request | None = None


def mask_id(customer: str) -> str:
    return "cust-" + hashlib.sha256(customer.encode()).hexdigest()[:8]


class Gateway:
    def __init__(self, count: Callable[[str], int], budgets: dict[str, int], config: GatewayConfig | None = None) -> None:
        if any(v < 0 for v in budgets.values()):
            raise ValueError("budgets cannot be negative")
        self.count = count
        self.cfg = config or GatewayConfig()
        self.budgets = dict(budgets)
        self.used: dict[str, int] = dict.fromkeys(budgets, 0)
        self.limiter = RequestRateLimiter(self.cfg.rps)
        self._open: dict[int, tuple[str, int]] = {}
        self._ids = itertools.count(1)
        self.log: list[str] = []

    def _input(self, req: Request) -> int:
        return account(req, self.count)["total"]

    def _trim(self, req: Request) -> tuple[Request, list[str], int]:
        req = copy.deepcopy(req)
        dropped: list[str] = []
        n = self._input(req)
        while n > self.cfg.input_cap and req.history:
            req.history = req.history[2:] if len(req.history) >= 2 else []
            dropped.append("history_turn")
            n = self._input(req)
        while n > self.cfg.input_cap and req.docs:
            req.docs = req.docs[:-1]
            dropped.append("doc")
            n = self._input(req)
        return req, dropped, n

    def _deny(self, customer: str, reason: str, n: int = 0) -> Decision:
        self.log.append(f"deny {mask_id(customer)} {reason} input={n}")
        return Decision(False, reason, input_tokens=n)

    def check(self, customer: str, req: Request, now: float, max_output: int | None = None) -> Decision:
        if customer not in self.budgets:
            return self._deny(customer, "unknown_customer")
        want = self.cfg.default_output if max_output is None else max_output
        if want <= 0:
            return self._deny(customer, "invalid_max_output")
        if not self.limiter.allow(now):
            return self._deny(customer, "rate_limited")
        n = self._input(req)
        trimmed: list[str] = []
        if n > self.cfg.input_cap:
            if self.cfg.mode == "reject":
                return self._deny(customer, "input_over_cap", n)
            req, trimmed, n = self._trim(req)
            if n > self.cfg.input_cap:
                return self._deny(customer, "input_over_cap_after_trim", n)
        # input_cap + min_output <= context_window (checked in config), so the reserve always fits.
        reserve = min(want, self.cfg.context_window - n)
        if self.used[customer] + n + reserve > self.budgets[customer]:
            return self._deny(customer, "token_budget_exceeded", n)
        self.used[customer] += n + reserve
        rid = next(self._ids)
        self._open[rid] = (customer, reserve)
        self.log.append(f"allow {mask_id(customer)} input={n} reserve={reserve} trimmed={len(trimmed)}")
        return Decision(True, "ok", n, reserve, trimmed, rid, req)

    def settle(self, reservation_id: int, actual_output: int) -> int:
        """Release the unused part of a reservation. Returns tokens released."""
        if actual_output < 0:
            raise ValueError("actual_output cannot be negative")
        if reservation_id not in self._open:
            raise KeyError("unknown or already settled reservation")
        customer, reserve = self._open.pop(reservation_id)
        if actual_output > reserve:
            raise ValueError("actual output exceeded the reservation")
        released = reserve - actual_output
        self.used[customer] -= released
        return released
