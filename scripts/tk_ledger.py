#!/usr/bin/env python3
"""Findings ledger: remembers what reviews caught so recurring mistakes can become machine rules.

WHAT:       `record` appends one JSON line per finding (PR id, rule, file, severity, confidence) to a ledger file;
            `candidates` returns proven rules seen in ≥ N different PRs, with where they happened — the input of
            tk-learn-rules.
WHY:        A mistake fixed once is a fix; a mistake seen twice is a missing rule. Memory must be a file, not a hope.
RUNS WHEN:  After tk-review (`record`) and when tk-learn-rules runs (`candidates`).
AFFECTS:    Appends to the ledger file only (default .trust-kitchen/ledger.jsonl in the reviewed repo).
CAUTION:    Unproven findings (confidence < 3) are stored but never become candidates. The ledger may hold file paths
            of a private repo: keep it inside that repo, never publish it.
CHANGED:    2026-11-20 · v0.1 · new
            2026-11-21 · confidence read like the merge gate (a missing value used to count as 4 = proven)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_gate import confidence  # noqa: E402  one definition of "proven" for the gate and the ledger

DEFAULT = Path(".trust-kitchen/ledger.jsonl")


def record(path: Path, pr: str, findings: Iterable[Dict[str, Any]]) -> int:
    """WHAT: append findings of one PR; returns how many lines were written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as fh:
        for f in findings:
            row = {"ts": int(time.time()), "pr": pr, "rule": f.get("rule"), "category": f.get("category"),
                   "file": f.get("file"), "line": f.get("line"), "severity": f.get("severity"),
                   "confidence": confidence(f.get("confidence"))}  # same rule as the gate: missing / words = 0
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def candidates(path: Path, min_count: int = 2, min_confidence: int = 3) -> List[Dict[str, Any]]:
    """WHAT: proven rules that appeared in ≥ min_count distinct PRs, most frequent first."""
    if not path.exists():
        return []
    by_rule: Dict[str, Dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("confidence", 0) < min_confidence:
            continue
        c = by_rule.setdefault(row["rule"], {"rule": row["rule"], "category": row.get("category"), "count": 0,
                                             "prs": [], "files": []})
        c["count"] += 1
        if row["pr"] not in c["prs"]:
            c["prs"].append(row["pr"])
        if row.get("file") and row["file"] not in c["files"]:
            c["files"].append(row["file"])
    out = [c for c in by_rule.values() if len(c["prs"]) >= min_count]
    for c in out:
        c["prs"].sort()
        c["files"].sort()
    return sorted(out, key=lambda c: (-c["count"], c["rule"]))


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Trust Kitchen findings ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("pr")
    r.add_argument("findings", help="JSON file: a list of findings or an object with a 'findings' list")
    c = sub.add_parser("candidates")
    c.add_argument("--min-count", type=int, default=2)
    for p in (r, c):
        p.add_argument("--ledger", type=Path, default=DEFAULT)
    a = ap.parse_args(argv)
    if a.cmd == "record":
        data = json.load(open(a.findings, encoding="utf-8"))
        items = data.get("findings", []) if isinstance(data, dict) else data
        print(f"recorded {record(a.ledger, a.pr, items)} finding(s) in {a.ledger}")
    else:
        # learned in a trial run (2026-11-20): say whether the ledger exists, so "[]" is never ambiguous
        print(json.dumps({"ledger": "present" if a.ledger.exists() else "missing",
                          "candidates": candidates(a.ledger, a.min_count)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
