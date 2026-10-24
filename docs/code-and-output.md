# Real code and its real output

All output below was captured from runs in this repo (Python 3.13, tiktoken 0.12.0).

## From-scratch BPE

```python
from tokacct.tokenizers import scratch_bpe
b = scratch_bpe()
ids = b.encode("The planner counts tokens.")
print(len(ids), [b.vocab[i].decode() for i in ids])
```

```text
6 ['The', ' planner', ' count', 's', ' tokens', '.']
```

## Same sentence, two vocabularies

```python
from tokacct.tokenizers import by_name
for n in ["cl100k_base", "o200k_base"]:
    print(n, by_name(n).count("దయచేసి నివేదికను పంపండి"))
```

```text
cl100k_base 42
o200k_base 10
```

## Where the tokens go (`tokacct demo`)

```text
tokenizer: o200k_base
  system              40 tokens    9.4%
  tools              163 tokens   38.3%
  docs               155 tokens   36.4%
  history             36 tokens    8.4%
  user                 9 tokens    2.1%
  format_overhead     23 tokens    5.4%
  total              426 tokens
```

## Gateway trim, reserve and settle

```python
from tokacct.gateway import Gateway, GatewayConfig
from tokacct.request import Request
from tokacct.tokenizers import by_name

g = Gateway(by_name("o200k_base").count, {"Pinecrest Legal": 5000}, GatewayConfig(input_cap=300))
hist = [("user", "Earlier question about invoices. " * 20), ("assistant", "Earlier answer about invoices. " * 20)] * 3
d = g.check("Pinecrest Legal", Request("You are a helpful assistant.", "What changed in clause 4?", history=hist), now=0.0, max_output=512)
print(d.allowed, d.reason, d.input_tokens, d.reserved_output, d.trimmed)
print(g.settle(d.reservation_id, 140), g.used)
print(g.log)
```

```text
True ok 238 512 ['history_turn', 'history_turn']
372 {'Pinecrest Legal': 378}
['allow cust-27f354ae input=238 reserve=512 trimmed=2']
```

The log line carries a hashed customer id and counts only, never message text.

## Ledger

```python
from tokacct.ledger import Prices
Prices().cost(20, 30), Prices().cost(8000, 1000)
# (Decimal('0.000055'), Decimal('0.0055'))  -- illustrative prices, $0.50 / $1.50 per million
```

The full tables are in [results.md](results.md).
