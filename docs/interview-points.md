# Interview points

- **Why do tokens and words differ?** Tokenizers split text into pieces learned from data. Frequent English words are one piece; code symbols, JSON punctuation and scripts that were rare in the training data split into many. Measured here: `cl100k_base` used 1.18 tokens per word on English and 11.81 on Telugu.
- **What does a newer, larger vocabulary buy?** `o200k_base` cut Telugu tokens from 685 to 144 and Hindi from 403 to 115 versus `cl100k_base` on the same samples, with English nearly unchanged (111 vs 109). Same price per token means a much cheaper bill for those users.
- **How does BPE work?** Start from bytes, count neighbouring pairs, merge the most frequent into a new id, repeat. Encoding replays merges in learned order. Byte fallback means nothing is ever unknown. (SentencePiece unigram without byte fallback does produce unknowns: 46-49% of Indic pieces here.)
- **What is in a prompt besides the question?** System prompt, history, tool schemas, retrieved docs and layout markers. In the RAG example the question was 2.1% of 426 input tokens; tool schemas were the biggest part at 38.3%.
- **How do you stop a bill blow-up before the call?** Count first; cap input with reject or trim; reserve output; charge per-customer token budgets, not just requests per second. In the replay, the 100 RPS limit stopped 104 of 1,200 requests and budgets stopped 314.
- **How do you know your count is right?** Reconcile with reported usage. Own tokenizer plus template: 0.0% drift on all four requests. Counting only content without layout: -5% to -21%. Counting only the user's text: -87% to -98%.
- **Why reserve then settle?** Output length is unknown; reserving the maximum keeps the budget safe, settling returns the unused part.
- **When are the quick rules OK?** Rough English sizing. They overestimated English by 15-38% and underestimated code, JSON, Indic text and emoji, by up to 62% on JSON.
- **Why Decimal in the ledger?** Ten thousand tiny charges summed exactly to $0.02 in the test; floats would drift.
