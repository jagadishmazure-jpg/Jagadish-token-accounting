"""Example requests used for accounting, the gateway replay and the local-model reconciliation."""

from __future__ import annotations

import random

from .request import Request

SYSTEM = (
    "You are the support assistant for Brightwell Home Goods. Answer in plain English, keep replies under "
    "120 words, never promise refunds yourself, and hand off to a human when the customer is upset."
)

TOOLS = [
    {
        "name": "lookup_order",
        "description": "Return status, items and delivery estimate for one order number.",
        "parameters": {"type": "object", "properties": {"order_no": {"type": "string"}}, "required": ["order_no"]},
    },
    {
        "name": "open_return",
        "description": "Start a return for one item in an order and email the label.",
        "parameters": {
            "type": "object",
            "properties": {"order_no": {"type": "string"}, "sku": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["order_no", "sku"],
        },
    },
    {
        "name": "handoff",
        "description": "Pass the conversation to a human agent with a one-line summary.",
        "parameters": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]},
    },
]

DOCS = [
    "Returns policy: unused items can be returned within 30 days of delivery. Opened kitchen items can be returned "
    "within 14 days if they are faulty. Refunds go back to the original payment method within 5 to 7 business days.",
    "Shipping: standard delivery takes 3 to 5 business days. Orders above 60 dollars ship free. Large furniture is "
    "delivered by a partner courier who calls the day before to book a two-hour window.",
    "Damaged items: ask the customer for a photo of the damage and the box. Offer a replacement first; if stock is "
    "out, offer a refund. Do not ask the customer to ship back broken glass.",
]

HISTORY = [
    ("user", "Hi, my order ORD-20931 still says processing after four days."),
    ("assistant", "Sorry about the wait. I can check that order for you. One moment while I look it up."),
    ("user", "Thanks. It was a set of six glasses and a teapot."),
    ("assistant", "The glasses shipped yesterday; the teapot is on back-order until next week."),
]


def scenarios() -> dict[str, Request]:
    return {
        "short_chat": Request(SYSTEM, "What are your opening hours on Sunday?"),
        "support_with_history": Request(SYSTEM, "Can the teapot be sent separately when it arrives?", history=list(HISTORY)),
        "agent_with_tools": Request(SYSTEM, "Please start a return for the teapot in ORD-20931.", history=list(HISTORY), tools=TOOLS),
        "rag_with_docs": Request(SYSTEM, "One glass arrived cracked. What happens now?", history=list(HISTORY[:2]), tools=TOOLS, docs=DOCS),
    }


CUSTOMERS = ("Harbor Lane Clinic", "Copperleaf Studios", "Northgate Tutors", "Pinecrest Legal")


def workload(n: int, seed: int = 7) -> list[tuple[float, str, Request, int]]:
    """n requests at a target 100 RPS: (time, customer, request, max_output). Mostly short; some pasted documents."""
    rng = random.Random(seed)
    base = scenarios()
    out = []
    for i in range(n):
        t = i / 110.0  # slightly above 100 RPS so the request limiter has work to do
        cust = rng.choice(CUSTOMERS)
        r = rng.random()
        if r < 0.70:
            req = base["short_chat"]
        elif r < 0.85:
            req = base["support_with_history"]
        elif r < 0.93:
            req = base["rag_with_docs"]
        else:
            pasted = " ".join(DOCS) * rng.randint(20, 60)
            req = Request(SYSTEM, "Summarise this contract for me: " + pasted, history=list(HISTORY))
        out.append((t, cust, req, rng.choice([256, 512, 1024])))
    return out
