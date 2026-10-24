"""Post-flight reconciliation: our pre-flight count vs the usage a local model reports.

Uses llama-cpp-python with a small open GGUF chat model (ChatML layout). Optional: if the package
or model file is missing, run_local() raises and nothing is invented.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from .request import Request, account

MODEL_ENV = "TOKACCT_GGUF"
DEFAULT_GGUF = Path.home() / ".cache" / "tokacct" / "qwen2.5-0.5b-instruct-q4_k_m.gguf"


def drift_pct(predicted: int, reported: int) -> float:
    if reported <= 0:
        raise ValueError("reported must be positive")
    return round(100 * (predicted - reported) / reported, 2)


def gguf_path() -> Path | None:
    p = Path(os.environ.get(MODEL_ENV, DEFAULT_GGUF))
    return p if p.is_file() else None


def run_local(requests: dict[str, Request], counters: dict[str, Callable[[str], int]], max_tokens: int = 48) -> dict:
    path = gguf_path()
    if path is None:
        raise FileNotFoundError(f"set {MODEL_ENV} to a GGUF chat model file")
    from llama_cpp import Llama

    llm = Llama(str(path), n_ctx=4096, seed=0, verbose=False)

    def model_count(t: str) -> int:
        return len(llm.tokenize(t.encode("utf-8"), add_bos=False, special=False))

    allc = {"model-own-tokenizer": model_count, **counters}
    rows = {}
    for name, req in requests.items():
        r = llm.create_chat_completion(messages=req.messages(), max_tokens=max_tokens, temperature=0)
        usage = r["usage"]
        text = r["choices"][0]["message"]["content"] or ""
        row = {"reported_prompt": usage["prompt_tokens"], "reported_completion": usage["completion_tokens"], "by_counter": {}}
        for cname, c in allc.items():
            pred = account(req, c)["total"]
            out_pred = c(text)
            row["by_counter"][cname] = {
                "predicted_prompt": pred,
                "prompt_drift_pct": drift_pct(pred, usage["prompt_tokens"]),
                "predicted_completion": out_pred,
                "completion_drift_pct": drift_pct(out_pred, max(usage["completion_tokens"], 1)),
            }
        naive = {
            "user_text_only": model_count(req.user),
            "content_without_framing": sum(model_count(m["content"]) for m in req.messages()),
        }
        row["naive_model_tokenizer"] = {k: {"predicted_prompt": v, "prompt_drift_pct": drift_pct(v, usage["prompt_tokens"])} for k, v in naive.items()}
        rows[name] = row
    return {"model": path.name, "rows": rows}
