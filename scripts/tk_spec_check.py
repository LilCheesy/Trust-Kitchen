#!/usr/bin/env python3
"""Spec checker: a spec has the fixed frame, and code / tests are tied to its acceptance criteria.

WHAT:       `validate SPEC.md` — id heading `# SPEC-<AREA>-<nnn>`, a known `Status:`, every required `##` section, every
            `AC-nn` names a test or command in `code`, no duplicate AC / EC ids.
            `anchors SPEC.md --root DIR` — finds `@spec: SPEC-<AREA>-<nnn>#AC-nn` tags under DIR: a tag naming a
            criterion the spec does not have is an error; a ticked criterion (`- [x]`) with no tag is an error; an
            unticked one with no tag is a warning. Prints JSON.
WHY:        A spec is the contract the code is judged against. If nothing checks it, it drifts into a description of
            whatever got built. This makes the SDD loop a machine rule (validate + verify-anchor).
RUNS WHEN:  By tk-spec before asking for approval, by tk-build before reporting, and in CI if the team wants it.
AFFECTS:    Reads only. Exit 1 when there is any error.
CAUTION:    Skips .git, node_modules, virtualenvs, build output and binary files. A tag inside the spec itself is not
            counted as an anchor. Headings are matched case-insensitively and must be exactly the names below.
CHANGED:    2026-11-21 · v0.3 · new (tests written first)
            2026-11-21 · multi-part ids (SPEC-ABC-DEF-012), found on a multi-part id
            2026-11-21 · ids written as code (`AC-01`) accepted; repeated tag errors printed once
            2026-11-21 · tag ids read as whole numbers (AC-0123 was read as AC-012)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SECTIONS = ["Context", "Current state", "Agent contract", "Scope", "Behaviour", "Edge cases",
            "Acceptance criteria", "Limits", "Files", "Test plan", "Decisions", "Log"]
STATUSES = {"DRAFT", "WAITING_APPROVAL", "APPROVED", "DONE"}
# ids may have several parts (SPEC-PAY-001, SPEC-ABC-DEF-012)
SPEC_ID = r"SPEC-(?:[A-Z0-9]+-)+\d{3}"
ID = re.compile(rf"^#\s+({SPEC_ID})\b", re.M)
STATUS = re.compile(r"^Status:\s*(\S+)", re.M)
# the id may be written as code (`AC-01`); the closing backtick is consumed so it never counts as a test
AC_LINE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*`?(AC-\d{2,3})\b`?(.*)$", re.M)
EC_LINE = re.compile(r"^\s*-\s*`?(EC-\d{2,3})\b", re.M)
TAG = re.compile(rf"@spec:?\s*({SPEC_ID})#(AC-\d+)\b")  # whole number: AC-0123 is not AC-012
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".tox", ".mypy_cache"}


def validate(text: str) -> List[str]:
    """WHAT: every problem with the frame of one spec (empty list = valid)."""
    errs: List[str] = []
    if not ID.search(text):
        errs.append("missing id heading: the first heading must be '# SPEC-<AREA>-<nnn>: <title>'")
    st = STATUS.search(text)
    if not st:
        errs.append("missing 'Status:' line")
    elif st.group(1) not in STATUSES:
        errs.append(f"status '{st.group(1)}' is not one of {sorted(STATUSES)}")
    heads = {h.strip().lower() for h in re.findall(r"^##\s+(.+?)\s*$", text, re.M)}
    for s in SECTIONS:
        if s.lower() not in heads:
            errs.append(f"missing section '{s}'")
    seen: Dict[str, int] = {}
    for _box, ac, rest in AC_LINE.findall(text):
        seen[ac] = seen.get(ac, 0) + 1
        if "`" not in rest:
            errs.append(f"{ac}: names no test or command (write it in `code`)")
    if not seen:
        errs.append("no acceptance criteria ('- [ ] AC-01 ... (`test_name`)')")
    errs += [f"{ac}: listed more than once" for ac, n in seen.items() if n > 1]
    ecs: Dict[str, int] = {}
    for ec in EC_LINE.findall(text):
        ecs[ec] = ecs.get(ec, 0) + 1
    errs += [f"{ec}: listed more than once" for ec, n in ecs.items() if n > 1]
    return errs


def _files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            yield Path(dirpath) / f


def anchors(spec: Path, root: Path) -> Dict[str, Any]:
    """WHAT: tie `@spec` tags under `root` to the criteria of `spec`; returns {spec, anchored, errors, warnings}."""
    text = spec.read_text(encoding="utf-8")
    m = ID.search(text)
    sid = m.group(1) if m else spec.stem
    crit = {ac: box.lower() == "x" for box, ac, _ in AC_LINE.findall(text)}
    anchored: Dict[str, List[str]] = {ac: [] for ac in crit}
    errors: List[str] = []
    spec_abs = spec.resolve()
    for f in sorted(_files(root)):
        if f.resolve() == spec_abs:
            continue
        try:
            body = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable: not code
        rel = f.relative_to(root).as_posix()
        for tag_spec, ac in TAG.findall(body):
            if tag_spec != sid:
                continue
            if ac not in crit:
                msg = f"{rel}: tag {sid}#{ac} points at a criterion that does not exist"
                if msg not in errors:  # one line per file and tag, however often it repeats
                    errors.append(msg)
            elif rel not in anchored[ac]:
                anchored[ac].append(rel)
    warnings: List[str] = []
    for ac, ticked in crit.items():
        if not anchored[ac]:
            (errors if ticked else warnings).append(
                f"{ac}: {'ticked (proven) but ' if ticked else ''}no @spec tag in any file")
    return {"spec": sid, "anchored": anchored, "errors": errors, "warnings": warnings}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Trust Kitchen spec checker")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("spec", type=Path)
    a = sub.add_parser("anchors")
    a.add_argument("spec", type=Path)
    a.add_argument("--root", type=Path, default=Path.cwd())
    args = ap.parse_args(argv)
    if args.cmd == "validate":
        errs = validate(args.spec.read_text(encoding="utf-8"))
        print(json.dumps({"spec": str(args.spec), "errors": errs}, indent=2, ensure_ascii=False))
        return 1 if errs else 0
    rep = anchors(args.spec, args.root)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 1 if rep["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
