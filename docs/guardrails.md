# Guardrails and security controls

| Control | Where | Test |
|---|---|---|
| 100 RPS sliding-window limit before any counting work | `ratelimit.py`, `Gateway.check` | `test_rate_limit_101st_request`, `test_rate_window_slides` |
| Input cap with explicit mode: reject, or trim oldest history then last docs; never trims the system prompt or the question | `Gateway._trim` | `test_trim_*`, `test_reject_mode_rejects_over_cap` |
| Output always reserved; config refuses an input cap that leaves less than `min_output` in the window | `GatewayConfig` | `test_bad_config`, `test_reserve_never_below_min_output_at_cap` |
| Per-customer token budgets charged up front with input plus reservation, settled after the call; double settle and over-reservation output are errors | `Gateway.settle` | `test_settle_*`, `test_budget_*` |
| Unknown customers denied | `Gateway.check` | `test_unknown_customer` |
| Negative, NaN or infinite prices rejected; token counts must be non-negative integers (bools refused) | `ledger.Prices` | `test_negative_or_bad_price_rejected`, `test_bad_token_counts` |
| Money in Decimal, no float drift | `ledger.py` | `test_decimal_no_float_drift` |
| Logs hold a hashed customer id and counts; denial reasons are fixed codes that never echo text | `Gateway._deny`, `mask_id` | `test_log_masks_customer_and_hides_text`, `test_reasons_never_echo_text` |
| PII masking helper (emails, phones, SSNs, Luhn-checked card numbers) and a repo-wide PII scan | `pii.py`, `test_repo_hygiene.py` | `test_redact`, `test_no_pii_in_tracked_text` |
| tiktoken special-token strings in user text are counted as plain text, not as control tokens | `tokenizers._tiktoken` | `test_special_token_text_is_counted_as_text` |
| Fictional-company check with a hashed blocklist | `scripts/check_brands.py` | `test_brand_check_clean` |
| Supply chain: pinned dependencies, SHA-pinned actions, Dependabot, CodeQL, gitleaks on full history | `.github/` | CI |
