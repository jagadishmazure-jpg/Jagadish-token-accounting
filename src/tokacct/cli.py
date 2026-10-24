"""tokacct bench | bench --check FILE | reconcile | chart | demo"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import tokenizers
from .compare import compare
from .corpus import CATEGORIES, SAMPLES
from .estimate import estimate_errors
from .replay import replay
from .request import account, shares
from .scenarios import scenarios


def bench() -> dict:
    counters = tokenizers.available()
    acct_counter = next((c for c in counters if c.name == "o200k_base"), counters[0])
    acct = {}
    for name, req in scenarios().items():
        parts = account(req, acct_counter.count)
        acct[name] = {"tokens": parts, "share_pct": shares(parts)}
    return {
        "tokenizers": [c.name for c in counters],
        "compare": compare(counters),
        "accounting_tokenizer": acct_counter.name,
        "accounting": acct,
        "estimate_error_pct": {c.name: estimate_errors(c) for c in counters if c.name != f"scratch-bpe-{tokenizers.BPE_VOCAB}"},
        "spm_unknown_pct": {cat: tokenizers.spm_unknown_share(SAMPLES[cat]) for cat in CATEGORIES} if tokenizers.spm_path() else None,
        "replay_trim": replay(acct_counter.count, mode="trim"),
        "replay_reject": replay(acct_counter.count, mode="reject"),
    }


def check(path: Path) -> int:
    want = json.loads(path.read_text())
    got = bench()
    bad = []
    for key in ("compare", "estimate_error_pct"):
        for name, val in got[key].items():
            if name in want[key] and want[key][name] != val:
                bad.append(f"{key}/{name}")
    if got["accounting_tokenizer"] == want["accounting_tokenizer"]:
        for key in ("accounting", "replay_trim", "replay_reject"):
            if got[key] != want[key]:
                bad.append(key)
    skipped = sorted(set(want["tokenizers"]) - set(got["tokenizers"]))
    if skipped:
        print(f"not installed here, skipped: {', '.join(skipped)}")
    if bad:
        print("mismatch:", ", ".join(bad))
        return 1
    print(f"results match for: {', '.join(got['tokenizers'])}")
    return 0


def reconcile() -> dict:
    from .reconcile import run_local

    cs = {c.name: c.count for c in tokenizers.available() if c.name in ("cl100k_base", "o200k_base")}
    return run_local(scenarios(), cs)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tokacct")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bench")
    b.add_argument("--check", type=Path)
    b.add_argument("--out", type=Path, default=Path("results.json"))
    r = sub.add_parser("reconcile")
    r.add_argument("--out", type=Path, default=Path("results_local_model.json"))
    sub.add_parser("chart")
    sub.add_parser("demo")
    a = p.parse_args(argv)
    if a.cmd == "bench":
        if a.check:
            return check(a.check)
        a.out.write_text(json.dumps(bench(), indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {a.out}")
    elif a.cmd == "reconcile":
        a.out.write_text(json.dumps(reconcile(), indent=2) + "\n")
        print(f"wrote {a.out}")
    elif a.cmd == "chart":
        from .charts import render_all

        for f in render_all(Path("results.json"), Path("results_local_model.json"), Path("docs/charts")):
            print(f"wrote {f}")
    else:
        from .scenarios import scenarios as sc

        c = tokenizers.by_name("o200k_base")
        req = sc()["rag_with_docs"]
        parts = account(req, c.count)
        print(f"tokenizer: {c.name}")
        for k, v in shares(parts).items():
            print(f"  {k:16} {parts[k]:5d} tokens  {v:5.1f}%")
        print(f"  {'total':16} {parts['total']:5d} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
