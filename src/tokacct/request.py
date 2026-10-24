"""Full request accounting: every part that is sent, not just the user's question.

Messages are rendered in a ChatML-style layout: each message is wrapped as
<|im_start|>{role}\\n{content}<|im_end|>\\n and the prompt ends with <|im_start|>assistant\\n.
The two markers are single special tokens in tokenizers that use this layout, so the per-message
overhead is 2 marker tokens plus the tokens of "{role}\\n" and the trailing "\\n".
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

TOOLS_HEADER = "You may call these tools. Reply with a JSON object naming the tool and its arguments.\n"
DOCS_HEADER = "Use only the context below to answer.\n"
MARKER_TOKENS = 2
PARTS = ("system", "tools", "docs", "history", "user", "format_overhead")


@dataclass
class Request:
    system: str
    user: str
    history: list[tuple[str, str]] = field(default_factory=list)
    tools: list[dict] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)

    def tools_text(self) -> str:
        if not self.tools:
            return ""
        return TOOLS_HEADER + "\n".join(json.dumps(t, separators=(",", ":"), sort_keys=True) for t in self.tools)

    def docs_text(self) -> str:
        if not self.docs:
            return ""
        return DOCS_HEADER + "\n\n".join(f"[doc {i + 1}] {d}" for i, d in enumerate(self.docs))

    def messages(self) -> list[dict[str, str]]:
        sys_parts = [p for p in (self.system, self.tools_text()) if p]
        msgs = [{"role": "system", "content": "\n\n".join(sys_parts)}]
        msgs += [{"role": r, "content": c} for r, c in self.history]
        user_parts = [p for p in (self.docs_text(), self.user) if p]
        msgs.append({"role": "user", "content": "\n\n".join(user_parts)})
        return msgs


def message_overhead(role: str, count: Callable[[str], int]) -> int:
    return MARKER_TOKENS + count(f"{role}\n") + count("\n")


def priming_overhead(count: Callable[[str], int]) -> int:
    return 1 + count("assistant\n")


def account(req: Request, count: Callable[[str], int]) -> dict[str, int]:
    """Tokens per part. Joiners (blank lines between parts) are booked as format overhead."""
    parts = {
        "system": count(req.system) if req.system else 0,
        "tools": count(req.tools_text()) if req.tools else 0,
        "docs": count(req.docs_text()) if req.docs else 0,
        "history": sum(count(c) for _, c in req.history),
        "user": count(req.user),
    }
    msgs = req.messages()
    content_total = sum(count(m["content"]) for m in msgs)
    framing = sum(message_overhead(m["role"], count) for m in msgs) + priming_overhead(count)
    parts["format_overhead"] = framing + (content_total - sum(parts.values()))
    parts["total"] = sum(parts[p] for p in PARTS)
    return parts


def shares(parts: dict[str, int]) -> dict[str, float]:
    total = parts["total"]
    if total <= 0:
        raise ValueError("total must be positive")
    return {p: round(100 * parts[p] / total, 2) for p in PARTS}
