#!/usr/bin/env python3
"""Merge gate: turns review facts into one verdict — MERGE, CHANGES_REQUESTED or NEEDS_HUMAN.

WHAT:       Applies a fixed, readable policy to the merged review result: deterministic checks, proven findings,
            runtime verification, restricted areas, diff size, reviewer conflicts, budget. Unproven findings
            (confidence < 3) are listed but never block. auto_merge is true only for MERGE when the repo opted in.
WHY:        The decision to merge must be a rule a person can read and test, not a model's mood.
RUNS WHEN:  Last step of tk-review (`python scripts/merge_gate.py facts.json [--policy .trust-kitchen/policy.json]`).
AFFECTS:    Prints the verdict JSON; exit 0 MERGE, 2 NEEDS_HUMAN (or unreadable input: then nothing is printed on
            stdout and stderr says why), 3 CHANGES_REQUESTED. Never merges anything itself.
CAUTION:    Restricted areas can never be auto-merged, whatever the policy says. Changing this file changes what
            ships without a person: treat it like production code.
CHANGED:    2026-11-20 · v0.1 · new
            2026-11-21 · size is advice by default (notes); a hard cap only when the policy sets max_lines
            2026-11-21 · only deterministic == "passed" may merge; dependencies + project paths restricted;
                         non-numeric confidence is unproven (independent review findings 1, 2, 11, 17)
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

# "dependencies": a version bump runs new third-party code; "restricted-path": paths the project declared in
# .trust-kitchen/config.json (restricted_paths), tagged by tk_scan --config. Both need a person (2026-11-21).
RESTRICTED_AREAS = {"auth", "security", "migration", "infra", "ci", "review-config", "dependencies", "restricted-path"}
# 2026-11-21: no hard size cap by default — small atomic PRs are advised (notes), not enforced.
# A team that wants a cap sets "max_lines" in its policy.
DEFAULT_POLICY = {"auto_merge": False, "max_lines": None, "min_confidence_to_block": 3}  # ASSUMED defaults
ADVISE_LINES = 400  # ASSUMED: above this, the verdict carries a note asking for atomic PRs
BLOCKING = {"BLOCKER", "MAJOR"}


def confidence(value: Any) -> int:
    """WHAT:       a finding's confidence as 0-5; anything that is not a whole number 1-5 is 0 (unproven).
    WHY:          Reviewer output often says "high" or leaves it out; that must never crash the gate or count as proof.
    RUNS WHEN:    decide(); scripts/tk_ledger.py uses the same rule.
    CHANGED:      2026-11-21 · new (a word used to crash the gate; the ledger used to treat "missing" as 4)"""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return n if 1 <= n <= 5 else 0


def decide(facts: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """WHAT: facts {deterministic, verify, changed_lines, areas, findings, conflicts?, budget_exhausted?, docs_only?}
    → {verdict, auto_merge, reasons, notes, blocking, unproven}. `notes` never change the verdict."""
    p = {**DEFAULT_POLICY, **(policy or {})}
    findings: List[Dict[str, Any]] = list(facts.get("findings") or [])
    notes: List[str] = []
    proven = [f for f in findings if confidence(f.get("confidence")) >= p["min_confidence_to_block"]]
    unproven = [f for f in findings if f not in proven]
    blocking = [f for f in proven if f.get("severity") in BLOCKING]
    bad_conf = [f for f in findings if confidence(f.get("confidence")) == 0 and f.get("confidence") not in (0, "0")]
    if bad_conf:
        notes.append(f"{len(bad_conf)} finding(s) without a numeric confidence 1-5: treated as unproven")
    change: List[str] = []
    human: List[str] = []

    det = facts.get("deterministic")
    if det == "failed":
        change.append("deterministic checks (build / lint / tests) are red")
    elif det != "passed":
        # only an explicit pass may merge: a timeout, a skip or a missing result proves nothing (2026-11-21)
        human.append(f"deterministic checks did not pass (deterministic={det})")
    for f in blocking:
        change.append(f"{f.get('severity')} {f.get('rule')} at {f.get('file')}:{f.get('line')}")

    areas = sorted(set(facts.get("areas") or []) & RESTRICTED_AREAS)
    if areas:
        human.append("touches restricted area(s): " + ", ".join(areas))
    verify = facts.get("verify")
    if verify != "passed" and not (verify == "not_applicable" and facts.get("docs_only")):
        human.append(f"behaviour not verified by a run (verify={verify})")
    lines = int(facts.get("changed_lines") or 0)
    if p["max_lines"] is not None and lines > p["max_lines"]:
        human.append(f"{lines} changed lines > {p['max_lines']} (team cap): split the PR")
    elif lines > ADVISE_LINES:
        notes.append(f"{lines} changed lines: prefer atomic PRs, one logical change each (advice, not a gate)")
    for c in facts.get("conflicts") or []:
        human.append(f"reviewers disagree: {c}")
    if facts.get("budget_exhausted"):
        human.append("review budget exhausted before every reviewer finished")

    if change:
        verdict = "CHANGES_REQUESTED"
    elif human:
        verdict = "NEEDS_HUMAN"
    else:
        verdict = "MERGE"
    reasons = change + human or ["all checks green, behaviour verified, no proven blocking finding"]
    return {"verdict": verdict, "auto_merge": verdict == "MERGE" and bool(p["auto_merge"]) and not areas,
            "reasons": reasons, "notes": notes, "blocking": blocking, "unproven": unproven}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Trust Kitchen merge gate")
    ap.add_argument("facts", help="JSON file with the merged review facts")
    ap.add_argument("--policy", help="JSON policy file (default: built-in, auto_merge off)")
    a = ap.parse_args(argv)
    # bad input is exit 2 with a one-line reason, never a traceback that a caller could misread (second review B12)
    try:
        facts = json.load(open(a.facts, encoding="utf-8"))
        policy = json.load(open(a.policy, encoding="utf-8")) if a.policy else None
        if not isinstance(facts, dict) or (policy is not None and not isinstance(policy, dict)):
            raise ValueError("facts and policy must be JSON objects")
        v = decide(facts, policy)
    except (OSError, ValueError, TypeError, AttributeError) as e:
        print(f"merge_gate: bad input: {e}", file=sys.stderr)
        return 2
    print(json.dumps(v, indent=2, ensure_ascii=False))
    return {"MERGE": 0, "NEEDS_HUMAN": 2, "CHANGES_REQUESTED": 3}[v["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
