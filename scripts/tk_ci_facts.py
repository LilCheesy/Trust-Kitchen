#!/usr/bin/env python3
"""CI facts: turns a scan result plus what the CI run proved into the facts the merge gate decides on.

WHAT:       Reads scan.json (tk_scan) and the policy, and these environment variables set by the workflow:
            TK_CHECKS=passed  (the project's build / lint / test steps ran and passed)
            TK_VERIFY=passed  (a step ran the real thing: end-to-end tests or the project's verify skill)
            TK_DISMISSED_BY   (login of the person who just added the `tk:dismiss` label to this PR)
            TK_HEAD_SHA       (the commit the run is about)
            Then: scanner MAJOR hits are pattern guesses and do not block unless the policy sets
            "ci_major_blocks": true; with a dismissal, BLOCKER / MAJOR scanner findings are kept, marked
            "dismissed by @<login> for <sha>", and stop blocking. Prints the facts JSON.
WHY:        Owner's decision (2026-11-21): no red check for pattern guesses by default; an explicit, recorded escape
            for false alarms; and a real path to MERGE when the checks and a real run passed. Kept in a tested script
            instead of workflow YAML.
RUNS WHEN:  In CI, after tk_scan: `python -I .trust-kitchen/scripts/tk_ci_facts.py scan.json --policy policy.json`.
AFFECTS:    Reads only. Exit 0 facts printed · 2 unreadable input (nothing decided).
CAUTION:    A dismissal never touches restricted areas or failed project checks: the gate still needs a person for
            those. It is valid only for the run started by adding the label; a new push needs a new dismissal.
            Only "passed", exactly, counts for TK_CHECKS / TK_VERIFY: anything else is "missing".
CHANGED:    2026-11-21 · new
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Mapping, Optional

BLOCKING = {"BLOCKER", "MAJOR"}
UNPROVEN = 2  # below the gate's min_confidence_to_block (3): shown, never blocking


def build(scan: Dict[str, Any], env: Mapping[str, str], policy: Dict[str, Any]) -> Dict[str, Any]:
    """WHAT: merge-gate facts for one CI run (see the module docstring for the inputs)."""
    major_blocks = bool(policy.get("ci_major_blocks", False))
    who = (env.get("TK_DISMISSED_BY") or "").strip()
    sha = (env.get("TK_HEAD_SHA") or "")[:7] or "this commit"
    notes: List[str] = []
    findings: List[Dict[str, Any]] = []
    for f in scan.get("findings", []):
        f = dict(f)
        sev = f.get("severity")
        if who and sev in BLOCKING:
            f["confidence"] = UNPROVEN
            f["why"] = f"{f.get('why', '')} (dismissed by @{who} for {sha} with the tk:dismiss label)"
        elif sev == "MAJOR" and not major_blocks:
            f["confidence"] = UNPROVEN
            f["why"] = f"{f.get('why', '')} (heuristic: confirm or dismiss in review)"
        findings.append(f)
    if who:
        notes.append(f"scanner findings dismissed by @{who} for {sha} (tk:dismiss label); a new push needs a new "
                     f"dismissal")
    stats = scan.get("stats", {})
    docs_only = bool(stats.get("docs_only"))
    checks = "passed" if env.get("TK_CHECKS") == "passed" else "missing"
    verify = "passed" if env.get("TK_VERIFY") == "passed" else ("not_applicable" if docs_only else "missing")
    return {"deterministic": checks, "verify": verify, "docs_only": docs_only,
            "changed_lines": stats.get("changed_lines", 0), "areas": scan.get("areas", []),
            "findings": findings, "notes": notes}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Trust Kitchen: CI facts for the merge gate")
    ap.add_argument("scan", help="scan.json written by tk_scan.py")
    ap.add_argument("--policy", help=".trust-kitchen/policy.json (reads ci_major_blocks)")
    a = ap.parse_args(argv)
    try:
        scan = json.load(open(a.scan, encoding="utf-8"))
        policy = json.load(open(a.policy, encoding="utf-8")) if a.policy else {}
        if not isinstance(scan, dict) or not isinstance(policy, dict):
            raise ValueError("scan and policy must be JSON objects")
        facts = build(scan, os.environ, policy)
    except (OSError, ValueError, TypeError, AttributeError) as e:
        print(f"tk_ci_facts: bad input: {e}", file=sys.stderr)
        return 2
    print(json.dumps(facts, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
