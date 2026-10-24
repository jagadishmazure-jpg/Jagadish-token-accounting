# Limitations and known gaps

- **Small evaluation set.** 30 self-written samples (5 per content type). Treat the ratios as regression checks and as direction, not as population statistics.
- **Cross-tokenizer reconciliation is approximate by nature.** The local model uses its own vocabulary. Counting with `cl100k_base` or `o200k_base` plus the template landed within 0.2-3.2% of the reported prompt tokens on these four English requests; on Hindi or Telugu the gap would be much larger (see the tokens-per-word table).
- **Only one chat layout is modelled** (ChatML-style markers). Other layouts add different per-message overhead; the model-own-tokenizer path picks this up, the generic formula does not.
- **The SentencePiece model is English-centric.** The T5 vocabulary has no Devanagari or Telugu pieces and lacks braces, so 49.4% of Hindi pieces and 46.4% of Telugu pieces were the unknown id. Its low token counts there mean "information thrown away", not efficiency. This is kept visible in `test_spm_results_recorded_with_unknown_share`.
- **The from-scratch BPE has only 256 merges** trained on about 3 KB of English, so it uses 2.4-9.1x as many tokens as `o200k_base` on the evaluation set. It exists to show the mechanism, not to compete.
- **Completion reconciliation is short** (max 48 output tokens per request). Completion drift for the other tokenizers ranges from 0% to -22% on these tiny replies.
- **Replay output lengths are simulated** (uniform between 20 and the reservation). The ledger figures from the replay are mechanics checks with illustrative prices, not a forecast.
- **Budgets and the rate limiter live in one process.** A real deployment with several gateway replicas needs a shared store.
- **Not run in CI:** the SentencePiece numbers and the local-model reconciliation (model downloads). Their results are committed and the tests check the recorded values; CI still exercises the adapter and the failure path.
