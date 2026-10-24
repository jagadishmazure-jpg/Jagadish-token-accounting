# ADR 0002: Reserve output up front, settle afterwards

**Status:** accepted

**Context.** Output length is unknown before the call, and output tokens are the more expensive ones.

**Decision.** Charge the budget with input plus the requested maximum output (capped by the context window), then release the unused part when the reply's real length is known.

**Consequences.** Budgets cannot be overrun by concurrent long replies. Customers may be refused while reservations are open even if they would not have used them; the replay shows this as `token_budget_exceeded`.
