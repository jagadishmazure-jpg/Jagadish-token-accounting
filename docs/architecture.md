# Architecture

```mermaid
flowchart TB
    subgraph tokenizers[tokacct.tokenizers]
        B[scratch BPE 512<br/>bpe.py]
        C1[cl100k_base]
        C2[o200k_base]
        SP[SentencePiece unigram 32k]
    end
    subgraph request[tokacct.request]
        RQ[Request: system, history, tools, docs, user]
        MS[messages - ChatML layout]
        AC[account: tokens per part + overhead]
    end
    subgraph gateway[tokacct.gateway]
        RL[RequestRateLimiter 100 RPS]
        CAP[input cap: reject or trim]
        RES[output reservation]
        BUD[per-customer budget]
        SET[settle]
    end
    LED[tokacct.ledger: Prices, Ledger]
    REC[tokacct.reconcile: llama.cpp local model]
    EST[tokacct.estimate: quick-rule error]
    tokenizers --> AC
    RQ --> MS --> AC --> CAP
    RL --> CAP --> RES --> BUD --> REC --> SET --> LED
    tokenizers --> EST
```

| Module | Job |
|---|---|
| `bpe.py` | Byte-level BPE: pre-split regex, pair counting, merges, encode, decode |
| `tokenizers.py` | One `Counter(name, count)` interface over every tokenizer; optional ones load only if installed |
| `corpus.py` | 30 evaluation samples in six content types, plus separate BPE training text |
| `compare.py` | Tokens per word and per character by type |
| `request.py` | Builds the exact messages sent and books every token to a part |
| `ratelimit.py`, `gateway.py` | Pre-flight checks, reservations and settlement |
| `reconcile.py` | Calls the local model and compares predicted with reported usage |
| `ledger.py` | Decimal cost per request, per customer and per month |
| `estimate.py` | Error of the 4-characters and 1.3-words rules |
| `replay.py` | Deterministic 1,200-request run through gateway and ledger |
| `charts.py`, `cli.py` | Charts, evidence board and the `tokacct` command |

Design choices are recorded in [adr/](adr/).
