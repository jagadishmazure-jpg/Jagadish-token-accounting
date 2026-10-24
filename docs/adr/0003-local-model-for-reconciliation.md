# ADR 0003: Reconcile against a small local model

**Status:** accepted

**Context.** The repo must be free and local; hosted APIs cost money and need keys.

**Decision.** Use llama.cpp (through llama-cpp-python) with a 0.5B instruct model in GGUF format, which reports `prompt_tokens` and `completion_tokens` like a hosted API.

**Consequences.** Drift numbers are real but specific to that model and its template. Downloads (about 490 MB) keep this out of CI; results are committed and tests check them.
