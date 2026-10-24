# ADR 0001: Count the rendered request, not the user's text

**Status:** accepted

**Context.** Budgets based on the user's message miss system prompts, history, tool schemas, retrieved passages and layout markers.

**Decision.** Build the exact message list once and count it part by part, booking layout tokens and joiners to `format_overhead` so the parts always sum to the total.

**Consequences.** Counts match what is sent; in the local run, own tokenizer plus template matched reported usage exactly. The layout formula must be kept in step with the model's chat template.
