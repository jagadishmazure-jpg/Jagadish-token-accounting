# How to run

## Offline core (what CI runs)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,charts]"
ruff check . && ruff format --check .
pytest -q
python scripts/count_tests.py          # prints "tests: N"
tokacct demo
tokacct bench --check results.json     # recomputes cl100k / o200k / scratch-BPE numbers and the replay
python scripts/render_docs.py --check  # README and docs/results.md match the results files
python scripts/check_brands.py
```

tiktoken downloads its two vocabulary files once on first use and caches them.

## Optional: SentencePiece comparison

Any SentencePiece `.model` file works. The committed numbers used the open T5-small `spiece.model` (unigram, 32k pieces, Apache-2.0) from the public open-model hub. Save it as `~/.cache/tokacct/spiece.model`, or point `TOKACCT_SPM_MODEL` at another file.

## Optional: local model reconciliation

```bash
pip install -e ".[local]"    # prebuilt CPU wheels exist for llama-cpp-python; otherwise it compiles
tokacct reconcile            # about 10 s on 8 CPU cores; writes results_local_model.json
```

The committed run used the open Qwen2.5 0.5B instruct model in GGUF format, 4-bit `q4_k_m` (Apache-2.0), from the public open-model hub, saved as `~/.cache/tokacct/qwen2.5-0.5b-instruct-q4_k_m.gguf` (or set `TOKACCT_GGUF`). Any small GGUF chat model that uses the ChatML layout works.

The model file is about 490 MB and needs about 1 GB of RAM. Then regenerate everything:

```bash
tokacct bench && tokacct chart && python scripts/render_docs.py
```

There is no cloud path; nothing here is billable.
