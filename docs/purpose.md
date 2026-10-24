# Purpose

Words and requests are the wrong units for LLM budgets. A model reads and bills tokens, and the number of tokens in a request depends on three things people tend to forget:

1. **The tokenizer.** The same sentence can be 10 tokens in one vocabulary and 42 in another (measured here on a short Telugu sentence: `o200k_base` 10, `cl100k_base` 42).
2. **Everything around the question.** System prompt, earlier turns, tool schemas, retrieved passages and the chat layout's own markers. In the RAG example here, the user's question is 2.1% of the input.
3. **The output.** It is unknown before the call, so it has to be reserved, then settled.

This repo is for:

- **Builders** who need a pre-flight check and a ledger they can read in an afternoon.
- **Reviewers and interviewers** who want measured answers to "how many tokens is that?", not guesses.
- **The owner's portfolio**, as the counting layer under [Jagadish-llm-capacity-planning](https://github.com/jagadishmazure-jpg/Jagadish-llm-capacity-planning).

Everything runs on a laptop with no paid service. All companies in the examples are invented.
