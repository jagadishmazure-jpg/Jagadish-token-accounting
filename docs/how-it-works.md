# How it works, step by step

1. **Tokenize.** `scratch_bpe()` trains a 512-id byte-level BPE on a short English and code text. The first 256 ids are raw bytes, so any input round-trips; the other 256 are merges learned by repeatedly joining the most frequent neighbouring pair. Real tokenizers are loaded behind the same interface.
2. **Compare.** For each of six content types (English, code, JSON, Hindi, Telugu, emoji) and each tokenizer, total tokens are divided by whitespace words and by characters.
3. **Build the real request.** `Request.messages()` produces exactly what the model receives: tools are serialised as compact JSON into the system message, retrieved passages are numbered and placed before the question in the user message.
4. **Account for it.** `account()` counts each part on its own, then counts the layout: two marker tokens per message, the role line, the trailing newline, the final assistant cue, and the blank lines that join parts. The parts always sum to the total.
5. **Pre-flight.** `Gateway.check()` runs in a fixed order: 100 RPS sliding window, input cap (reject, or trim the oldest history turns first and the last retrieved passage next), output reservation, then the customer's token budget, which is charged with input plus reserved output.
6. **Call and reconcile.** `reconcile.run_local()` sends the same messages to a 0.5B chat model through llama.cpp and compares the reported `prompt_tokens` and `completion_tokens` with our counts.
7. **Settle and bill.** `settle()` gives back the unused reservation. `Ledger.record()` prices input and output separately with Decimal and rolls costs up by customer and month.
8. **Check the quick rules.** `estimate_errors()` compares the two common shortcuts with the real counts per content type.
