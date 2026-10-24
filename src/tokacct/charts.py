"""Charts and the evidence board, drawn from results files only."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .corpus import CATEGORIES  # noqa: E402


def _bars(ax, data: dict[str, dict[str, float]], title: str, ylabel: str) -> None:
    names = list(data)
    w = 0.8 / len(names)
    for i, n in enumerate(names):
        ax.bar([x + i * w for x in range(len(CATEGORIES))], [data[n][c] for c in CATEGORIES], w, label=n)
    ax.set_xticks([x + 0.4 - w / 2 for x in range(len(CATEGORIES))], CATEGORIES)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=7)


def render_all(results: Path, local: Path, outdir: Path) -> list[Path]:
    res = json.loads(results.read_text())
    outdir.mkdir(parents=True, exist_ok=True)
    out = []
    tpw = {n: {c: v[c]["tokens_per_word"] for c in CATEGORIES} for n, v in res["compare"].items()}
    est = res["estimate_error_pct"]["o200k_base"]
    err = {"4 chars/token": {c: est[c]["chars_rule"] for c in CATEGORIES}, "1.3 tokens/word": {c: est[c]["words_rule"] for c in CATEGORIES}}

    fig, ax = plt.subplots(figsize=(9, 4))
    _bars(ax, tpw, "Tokens per word by tokenizer and content type", "tokens / word")
    fig.tight_layout()
    fig.savefig(p := outdir / "tokens_per_word.png", dpi=120)
    plt.close(fig)
    out.append(p)

    fig, ax = plt.subplots(figsize=(9, 4))
    _bars(ax, err, "Rule-of-thumb error vs o200k_base (signed %)", "error %")
    ax.axhline(0, color="black", lw=0.8)
    fig.tight_layout()
    fig.savefig(p := outdir / "estimate_error.png", dpi=120)
    plt.close(fig)
    out.append(p)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    _bars(axes[0][0], tpw, "Tokens per word", "tokens / word")
    _bars(axes[0][1], err, "Quick-rule error vs o200k_base", "error %")
    axes[0][1].axhline(0, color="black", lw=0.8)
    acct = res["accounting"]["rag_with_docs"]["share_pct"]
    axes[1][0].barh(list(acct), list(acct.values()), color="#4c72b0")
    axes[1][0].set_title(f"Where the tokens go: RAG request ({res['accounting']['rag_with_docs']['tokens']['total']} tokens)")
    axes[1][0].set_xlabel("% of input tokens")
    ax = axes[1][1]
    ax.axis("off")
    lines = ["Gateway replay (1,200 requests, trim mode)"]
    lines += [f"  {k}: {v}" for k, v in res["replay_trim"]["outcomes"].items()]
    lines.append(f"  bill: ${res['replay_trim']['total_cost_usd']} (illustrative prices)")
    if local.is_file():
        loc = json.loads(local.read_text())
        lines.append("")
        lines.append(f"Local model reconciliation ({loc['model']})")
        for name, row in loc["rows"].items():
            d = {k: v["prompt_drift_pct"] for k, v in row["by_counter"].items()}
            lines.append(
                f"  {name}: reported {row['reported_prompt']}; drift "
                + ", ".join(f"{k.replace('_base', '').replace('-own-tokenizer', '')} {v:+}%" for k, v in d.items())
            )
    ax.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=7.5)
    fig.suptitle("Jagadish-token-accounting: evidence board (all numbers from real runs)", fontsize=14)
    fig.tight_layout()
    fig.savefig(p := outdir / "evidence_board.png", dpi=110)
    plt.close(fig)
    out.append(p)
    return out
