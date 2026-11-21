#!/usr/bin/env python3
"""Repo rule: every skill and agent is well-formed and documented in the README.

WHAT:       For skills/*/SKILL.md and agents/*.md: frontmatter has `name` (kebab-case, matches the folder / file,
            ≤ 64 chars) and `description` (non-empty, ≤ 1024 chars); body is not empty; every skill name appears in
            README.md; every `tk-*` name written in skills, references, agents or README is a real skill or agent.
            Prints one line per problem.
WHY:        Docs drift and broken skills are caught by a machine on every change, not by someone remembering.
RUNS WHEN:  `python scripts/check_skills.py` in CI and before every commit; tests/test_repo_rules.py runs it.
AFFECTS:    Reads only. Exit 1 when any problem is found.
CAUTION:    The frontmatter parser handles the simple `key: value` form used in this repo, not full YAML.
CHANGED:    2026-11-20 · v0.1 · new
            2026-11-20 · learned rule: references to non-existent skills are reported
            2026-11-20 · v0.2: required sections for skills (7) and personas (Role / Menu / Rules)
            2026-11-20 · v0.3: hub `## Commands` table — present, unique commands, every target a real skill
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# v0.2 (2026-11-20): every skill / persona follows one strict frame, checked here rather than trusted to memory
SKILL_SECTIONS = ["When to use", "Inputs", "Procedure", "Output", "Rules", "Stop and ask", "Next"]
PERSONA_SECTIONS = ["Role", "Menu", "Rules"]
REF = re.compile(r"`(tk-[a-z0-9-]+)`")  # a skill / agent name written as code in docs
CMD_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|\s*`(tk[a-z0-9-]*)`", re.M)  # | `review` | `tk-review` | ...


def hub_commands(hub_text: str) -> List[Tuple[str, str]]:
    """WHAT:       (command, skill) rows of the hub's `## Commands` table, in order; [] when there is no such section.
    WHY:          v0.3 — `/tk review 42` dispatches by this table, so the table itself is checked by machine.
    RUNS WHEN:    check() below; tests/test_repo_rules.py.
    AFFECTS:      Read-only. The hub skill (skills/tk/SKILL.md) is the only file with this table.
    CAUTION:      Only rows whose first two cells are `code` are read; prose rows are ignored on purpose.
    CHANGED:      2026-11-20 · v0.3 · new"""
    m = re.search(r"^##\s+Commands\s*$(.*?)(?=^##\s|\Z)", hub_text, re.M | re.S)
    return CMD_ROW.findall(m.group(1)) if m else []


def _front(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    meta: Dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, text[end + 4:]


def _check_doc(path: Path, expected: str, kind: str) -> List[str]:
    meta, body = _front(path.read_text(encoding="utf-8"))
    errs = []
    name = meta.get("name", "")
    if not name:
        errs.append(f"{kind} {expected}: missing name")
    elif name != expected:
        errs.append(f"{kind} {expected}: name '{name}' does not match folder/file '{expected}'")
    if not KEBAB.match(expected) or len(expected) > 64:
        errs.append(f"{kind} {expected}: name must be kebab-case, ≤ 64 chars")
    desc = meta.get("description", "")
    if not desc:
        errs.append(f"{kind} {expected}: missing description")
    elif len(desc) > 1024:
        errs.append(f"{kind} {expected}: description longer than 1024 chars")
    if not body.strip():
        errs.append(f"{kind} {expected}: empty body")
        return errs
    heads = {m.strip().lower() for m in re.findall(r"^##\s+(.+?)\s*$", body, re.M)}
    for sec in (SKILL_SECTIONS if kind == "skill" else PERSONA_SECTIONS):
        if sec.lower() not in heads:
            errs.append(f"{kind} {expected}: missing section '{sec}'")
    return errs


def check(root: Path) -> List[str]:
    """WHAT: all problems in the repo at `root` (empty list = clean)."""
    errs: List[str] = []
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    for sk in sorted((root / "skills").glob("*/SKILL.md")):
        name = sk.parent.name
        errs += _check_doc(sk, name, "skill")
        if f"`{name}`" not in readme:
            errs.append(f"skill {name}: not documented in README.md")
    for ag in sorted((root / "agents").glob("*.md")) if (root / "agents").exists() else []:
        errs += _check_doc(ag, ag.stem, "agent")
    # Learned rule (2026-11-20): docs named a skill (tk-spec) that did not exist yet. Every `tk-*` named in a skill,
    # agent or the README must be a real skill or agent, so instructions never point an agent at nothing.
    known = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    known |= {p.stem for p in (root / "agents").glob("*.md")} if (root / "agents").exists() else set()
    docs = list((root / "skills").glob("*/SKILL.md")) + list((root / "skills").glob("*/references/*.md"))
    docs += list((root / "agents").glob("*.md")) if (root / "agents").exists() else []
    docs += [root / "README.md"] if (root / "README.md").exists() else []
    docs += [root / "installer" / "block.md"] if (root / "installer" / "block.md").exists() else []
    for doc in sorted(docs):
        for ref in sorted(set(REF.findall(doc.read_text(encoding="utf-8"))) - known):
            errs.append(f"{doc.relative_to(root).as_posix()}: names skill '{ref}' which does not exist")
    # Learned rule (2026-11-20, from a trial run): the hub `tk` must name every skill, or users cannot find it.
    hub = root / "skills" / "tk" / "SKILL.md"
    if hub.exists():
        hub_text = hub.read_text(encoding="utf-8")
        named = set(REF.findall(hub_text))
        for sk in sorted({p.parent.name for p in (root / "skills").glob("*/SKILL.md")} - named - {"tk"}):
            errs.append(f"skill {sk}: not reachable from the hub (skills/tk/SKILL.md never names it)")
        # v0.3 (2026-11-20): `/tk <command>` must land on a real skill, and one command means one thing
        rows = hub_commands(hub_text)
        if not rows:
            errs.append("skill tk: hub has no '## Commands' table, so `/tk <command>` cannot dispatch")
        seen: Dict[str, str] = {}
        for cmd, target in rows:
            if cmd in seen:
                errs.append(f"skill tk: command '{cmd}' is listed more than once")
            seen[cmd] = target
            if target not in known:
                errs.append(f"skill tk: command '{cmd}' points at '{target}', which is not a skill")
    return errs


if __name__ == "__main__":
    problems = check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    for p in problems:
        print(p)
    print(f"{'FAIL' if problems else 'OK'}: {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)
