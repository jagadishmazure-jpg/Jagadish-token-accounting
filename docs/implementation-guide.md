# Implementation guide (for adopters)

1. **Pick the counter that matches your model.** If you can load the model's own tokenizer, use it: in the local run, own tokenizer plus template matched the reported prompt tokens exactly. If you cannot, a modern open BPE vocabulary plus the template formula was within a few percent for English here; add a safety margin (for example 10%) and widen it for non-Latin scripts.
2. **Count the request you actually send.** Build messages once (`Request.messages()`) and count that, including tool schemas and retrieved passages. Never count only the user's text; that missed 87-98% of the prompt in the local run.
3. **Model the layout overhead.** Per message: markers + role line + separators; plus the final assistant cue. Check it once against your model's reported usage and adjust `message_overhead()`.
4. **Gate before the call.** Order: cheap rate check, input cap, output reservation, budget. Choose reject or trim per route: trimming is right for chat history, wrong for a contract the user asked you to review in full.
5. **Reserve then settle.** Charge input plus the requested maximum output, then give back the unused part when the reply ends. This prevents a burst of long replies from overrunning a budget.
6. **Reconcile continuously.** Log predicted vs reported tokens per request (counts only, no text) and alert when drift moves; a template or tokenizer change shows up there first.
7. **Bill with Decimal and separate prices.** Keep input and output prices apart, store the as-of date, reject negative values.
8. **Don't plan with the quick rules for non-English or structured text.** Measured error ran from +38% (English) to -62% (JSON, 1.3-words rule) against `o200k_base`.

## Swapping parts

| Need | Change |
|---|---|
| Another tokenizer | Add a `Counter` in `tokenizers.available()` |
| Another chat layout | Replace `message_overhead()` / `priming_overhead()` |
| Shared budgets across replicas | Move `Gateway.used` and the limiter to a shared store with atomic increments |
| Real prices | Construct `Prices(input_per_million=..., output_per_million=..., as_of=...)` |
