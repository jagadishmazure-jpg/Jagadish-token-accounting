# Threat model (STRIDE + OWASP LLM Top 10 where relevant)

| Threat | Example | Control |
|---|---|---|
| Spoofing | Caller claims another customer's id to spend their budget | Gateway only knows configured customers; authentication is the caller's job and is out of scope (documented) |
| Tampering | Edited `results.json` to make docs look better | `tokacct bench --check` recomputes and fails on mismatch in CI |
| Repudiation | Disputed bill | Ledger keeps per-request entries with input and output tokens and prices |
| Information disclosure | Prompt text or PII in logs and errors | Logs hold hashed ids and counts; denial reasons are fixed codes; PII helper and repo-wide scan |
| Denial of service / **LLM10 unbounded consumption** | Huge pasted documents, long outputs, bursts | Input cap, output reservation, per-customer token budgets, 100 RPS limit |
| Elevation of privilege | Special-token strings in user text treated as control tokens | tiktoken counted with special tokens disabled; test covers it |
| **LLM01 prompt injection** in retrieved docs | A passage tells the model to ignore rules | Out of scope for counting; docs are placed in the user turn, not the system turn, and the trim step drops docs before touching the question |
| **LLM03 supply chain** | Malicious dependency or action | Pinned versions, SHA-pinned actions, Dependabot, CodeQL, gitleaks |
