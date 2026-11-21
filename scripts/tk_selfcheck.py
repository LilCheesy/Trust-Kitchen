#!/usr/bin/env python3
"""Self-check: proves the installed review scripts work in this project, by making them catch known problems.

WHAT:       Runs the scanner on a planted bad diff (must report a secret, exit 1) and a clean diff (exit 0), the merge
            gate on known facts (clean → MERGE, red checks → CHANGES_REQUESTED, unknown checks → NEEDS_HUMAN, auto-merge
            only on opt-in), and reads .trust-kitchen/config.json and policy.json if present. One line per check.
WHY:        A check that cannot fail proves nothing. tk-setup ends with this, so "setup done" means the tools bite.
RUNS WHEN:  `python .trust-kitchen/scripts/tk_selfcheck.py` (tk-setup, last step; any time something looks off).
AFFECTS:    Reads only; runs the scripts next to it in a subprocess. Exit 0 all OK · 1 a check failed.
CAUTION:    The planted secret is built at runtime and never written to disk. A config that is missing is reported as
            "not set up yet", not as a failure: tk-setup writes it.
CHANGED:    2026-11-21 · new (replaces a repo-maintenance check that passed while checking nothing)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def _patch(path: str, line: str) -> str:
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1,0 +1,1 @@\n+{line}\n"


def _scan(diff: str):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.patch"
        p.write_text(diff, encoding="utf-8")
        r = subprocess.run([sys.executable, str(HERE / "tk_scan.py"), "--diff", str(p)], capture_output=True,
                           text=True, encoding="utf-8")
    try:
        return r.returncode, json.loads(r.stdout)
    except ValueError:
        return r.returncode, {"findings": []}


def main() -> int:
    results = []
    fake = "AKIA" + "Q7XW2" + "LMNOPQRSTUV"  # matches the AWS key shape; built here, never stored
    code, out = _scan(_patch("src/settings.py", f"KEY = '{fake}'"))
    results.append(("scanner catches a planted secret",
                    code == 1 and any(f.get("rule") == "secret" for f in out.get("findings", []))))
    code, out = _scan(_patch("src/util.py", "def add(a, b):"))
    results.append(("scanner stays quiet on clean code", code == 0 and not out.get("findings")))
    try:
        import merge_gate as mg
        clean = {"deterministic": "passed", "verify": "passed", "changed_lines": 10, "areas": [], "findings": []}
        ok = (mg.decide(clean)["verdict"] == "MERGE"
              and mg.decide({**clean, "deterministic": "failed"})["verdict"] == "CHANGES_REQUESTED"
              and mg.decide({**clean, "deterministic": "inconclusive"})["verdict"] == "NEEDS_HUMAN"
              and mg.decide(clean)["auto_merge"] is False
              and mg.decide({**clean, "areas": ["auth"]}, {"auto_merge": True})["auto_merge"] is False)
    except Exception as e:  # any import or logic error is a failed check, reported, never a traceback
        ok = False
        print(f"merge gate error: {e}")
    results.append(("merge gate", ok))
    for label, good in results:
        print(f"{label}: {'OK' if good else 'FAIL'}")
    cfg = HERE.parent / "config.json"
    if cfg.exists():
        c = json.loads(cfg.read_text(encoding="utf-8"))
        print(f"config: commands {sorted(k for k, v in (c.get('commands') or {}).items() if v)} · "
              f"restricted_paths {c.get('restricted_paths') or []}")
    else:
        print("config: not set up yet (run tk-setup)")
    pol = HERE.parent / "policy.json"
    print(f"policy: {json.loads(pol.read_text(encoding='utf-8')) if pol.exists() else 'missing (defaults)'}")
    return 0 if all(g for _, g in results) else 1


if __name__ == "__main__":
    sys.exit(main())
