#!/usr/bin/env python3
"""Trust Kitchen installer (Python): install, update, status and uninstall for any supported coding agent.

WHAT:       Copies the skills to where each chosen agent looks for them (installer/targets.json), the reviewer
            personas for agents that support subagents, the scripts to .trust-kitchen/scripts, the eval runner and
            example cases to .trust-kitchen/evals, a default merge policy (only if none exists), `/tk` command files
            where an agent needs one, and a marked block into AGENTS.md / agent rule files. Records every written
            file (with its sha256) and every folder it created in .trust-kitchen/install.json, so uninstall removes
            exactly that and nothing else.
WHY:        "Install and it runs" in any agent, without Node; and a clean, honest uninstall.
RUNS WHEN:  `python installer/install.py install --agents claude-code,codex [--dir PATH] [--yes]` (also: update,
            status, uninstall, list). The Node CLI (bin/trust-kitchen.js) does the same from targets.json.
AFFECTS:    Writes inside the target project only. Never overwrites a file it did not write, or one the user changed
            after install (reported as skipped); never deletes a changed file (reported as kept) or a folder the user
            already had; never edits outside the marked block of files the user already had, and keeps their line
            endings.
CAUTION:    Re-installing overwrites Trust Kitchen's own unchanged files (that is how update works). To customise a
            skill, copy it under a new name. Exit codes: 0 ok · 1 nothing installed (update) · 2 bad input.
CHANGED:    2026-11-20 · v0.2 · new
            2026-11-20 · text files written with LF on every OS (on Windows they were CRLF, unlike the Node installer)
            2026-11-20 · v0.3: `/tk` command files for agents that need them (_put_commands); skipped ones reported
            2026-11-21 · first independent review: eval runner installed; user files never overwritten; edited
                         files kept on uninstall (sha256 in the manifest); forgiving CLI input, exit 2, no tracebacks
            2026-11-21 · second review: example eval cases installed (local results never); `update` keeps files
                         the user edited; the user's CRLF kept; only folders the installer created are removed;
                         no TTY and a corrupt manifest exit 2
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
START, END = "<!-- trust-kitchen:start -->", "<!-- trust-kitchen:end -->"


def _targets(source: Path) -> Dict[str, Any]:
    return json.loads((source / "installer" / "targets.json").read_text(encoding="utf-8"))


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class _Run:
    """WHAT: what one install run has written, skipped and created, plus the previous manifest it must respect."""

    def __init__(self, project: Path, prev: Dict[str, Any]) -> None:
        self.project, self.prev = project, prev
        self.files: List[str] = []
        self.skipped: List[str] = []
        self.created_dirs: List[str] = []

    def rel(self, p: Path) -> str:
        return p.relative_to(self.project).as_posix()

    def mine(self, rel: str, out: Path) -> bool:
        """May Trust Kitchen write `rel`? Only if it does not exist, or Trust Kitchen wrote it and the user has not
        changed it since (the recorded sha256 still matches)."""
        if not out.exists() or rel in self.files:
            return True
        if rel not in self.prev.get("files", []):
            return False  # the user's own file
        recorded = self.prev.get("hashes", {}).get(rel)
        return recorded is None or _sha(out) == recorded

    def ensure_dir(self, d: Path) -> None:
        """Create `d` and record every folder that did not exist before, so uninstall removes only those."""
        missing = []
        while d != self.project and not d.exists():
            missing.append(d)
            d = d.parent
        for m in reversed(missing):
            m.mkdir()
            self.created_dirs.append(self.rel(m))

    def copy_file(self, src: Path, out: Path) -> None:
        rel = self.rel(out)
        if not self.mine(rel, out):
            self.skipped.append(rel)
            return
        self.ensure_dir(out.parent)
        shutil.copyfile(src, out)
        if rel not in self.files:
            self.files.append(rel)

    def copy_tree(self, src: Path, dst: Path, skip: tuple = ()) -> None:
        for f in sorted(src.rglob("*")):
            parts = f.relative_to(src).parts
            if f.is_file() and "__pycache__" not in parts and not (parts and parts[0] in skip):
                self.copy_file(f, dst / f.relative_to(src))

    def write_text(self, out: Path, text: str) -> None:
        rel = self.rel(out)
        if not self.mine(rel, out):
            self.skipped.append(rel)
            return
        self.ensure_dir(out.parent)
        out.write_text(text, encoding="utf-8", newline="\n")
        if rel not in self.files:
            self.files.append(rel)


def _read_keep_eol(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:  # keep the user's CRLF: same bytes as the Node installer
        return fh.read()


def _write_keep_eol(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _put_block(run: _Run, path: Path, body: str, front: str = "") -> bool:
    """WHAT: insert / replace the marked block; returns True when the file did not exist before."""
    created = not path.exists()
    old = "" if created else _read_keep_eol(path)
    block = f"{START}\n{body.strip()}\n{END}\n"
    if START in old and END in old:
        new = old[:old.index(START)] + block + old[old.index(END) + len(END):].lstrip("\r\n")
    else:
        eol = "\r\n" if "\r\n" in old else "\n"  # separate with the file's own line ending
        new = (front if created else "") + (old.rstrip() + eol + eol if old.strip() else "") + block
    run.ensure_dir(path.parent)
    _write_keep_eol(path, new)
    return created


def _drop_block(path: Path) -> None:
    if not path.is_file():
        return
    text = _read_keep_eol(path)
    if START in text and END in text:
        eol = "\r\n" if "\r\n" in text[:text.index(START)] else "\n"
        text = text[:text.index(START)].rstrip() + eol + text[text.index(END) + len(END):].lstrip("\r\n")
        _write_keep_eol(path, text if text.strip() else "")


def install(project: Path, agents: List[str], source: Path = HERE.parent) -> Dict[str, Any]:
    """WHAT: install for `agents` into `project`; returns {written, agents, skills_dirs, skipped}."""
    t = _targets(source)
    unknown = [a for a in agents if a not in t["agents"]]
    if unknown or not agents:
        raise ValueError(f"unknown or no agent(s): {', '.join(unknown) or '(none)'}; "
                         f"choose from {', '.join(t['agents'])}")
    project.mkdir(parents=True, exist_ok=True)
    always = t["always"]
    mpath = project / always["manifest"]
    prev = _load_manifest(mpath) if mpath.exists() else {}
    run = _Run(project, prev)
    blocks: List[str] = []
    created_blocks: List[str] = []
    skills_dirs: List[str] = []
    for a in agents:
        spec = t["agents"][a]
        sd = spec.get("skills_dir")
        if sd and sd not in skills_dirs:
            skills_dirs.append(sd)
            run.copy_tree(source / "skills", project / sd)
        if spec.get("agents_dir"):
            run.copy_tree(source / "agents", project / spec["agents_dir"])
    if any(not t["agents"][a].get("skills_dir") for a in agents):
        skills_dirs.append(always["fallback_skills_dir"])
        run.copy_tree(source / "skills", project / always["fallback_skills_dir"])
    run.copy_tree(source / "scripts", project / always["scripts_dir"])
    ev = always["evals"]
    run.copy_tree(source / ev["from"], project / ev["to"], skip=tuple(ev.get("skip", [])))
    policy = project / always["policy"]
    if not policy.exists():
        run.copy_file(source / "schema" / "policy.example.json", policy)
    body = (source / "installer" / "block.md").read_text(encoding="utf-8").replace(
        "{skills_dirs}", ", ".join(f"`{d}/`" for d in skills_dirs))
    targets_for_block = [(always["agents_md"], "")]
    for a in agents:
        for r in t["agents"][a].get("rules", []):
            targets_for_block.append((r["path"], r.get("front", "")))
    for rel, front in targets_for_block:
        if rel in blocks:
            continue
        if _put_block(run, project / rel, body, front):
            created_blocks.append(rel)
        blocks.append(rel)
    _put_commands(run, agents, t)
    hashes = {**prev.get("hashes", {}), **{r: _sha(project / r) for r in run.files}}
    run.ensure_dir(mpath.parent)
    manifest = {
        "version": t["version"],
        "agents": sorted(set(prev.get("agents", [])) | set(agents), key=list(t["agents"]).index),
        "files": sorted(set(prev.get("files", [])) | set(run.files)),
        "hashes": dict(sorted(hashes.items())),
        "blocks": sorted(set(prev.get("blocks", [])) | set(blocks)),
        "created_blocks": sorted(set(prev.get("created_blocks", [])) | set(created_blocks)),
        "created_dirs": sorted(set(prev.get("created_dirs", [])) | set(run.created_dirs)),
    }
    mpath.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"written": len(set(run.files)), "agents": manifest["agents"], "skills_dirs": skills_dirs,
            "skipped": sorted(set(run.skipped))}


def _put_commands(run: _Run, agents: List[str], t: Dict[str, Any]) -> None:
    """WHAT:       write each chosen agent's `/tk` command file (targets.json "commands"), with {skills_dir} filled in.
    WHY:          v0.3 — one "/tk" command in every agent, like a built-in slash command; Gemini CLI and OpenCode do
                  not run skills as slash commands, so a one-file command loads the hub and passes the arguments.
    RUNS WHEN:    install() / update, after the skills are copied.
    AFFECTS:      Adds the paths to run.files (so uninstall removes them); a user's own file is skipped.
    CAUTION:      bin/trust-kitchen.js mirrors this.
    CHANGED:      2026-11-20 · v0.3 · new"""
    for a in agents:
        spec = t["agents"][a]
        sd = spec.get("skills_dir") or t["always"]["fallback_skills_dir"]
        for cmd in spec.get("commands", []):
            run.write_text(run.project / cmd["path"], cmd["text"].replace("{skills_dir}", sd))


def _load_manifest(mpath: Path) -> Dict[str, Any]:
    try:
        m = json.loads(mpath.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ValueError(f"{mpath} is not valid JSON ({e}); fix or delete it") from None
    if not isinstance(m, dict):
        raise ValueError(f"{mpath} is not a Trust Kitchen manifest")
    return m


def uninstall(project: Path) -> Dict[str, Any]:
    """WHAT: remove the files and blocks listed in the manifest, except files changed since install (kept and
    reported); remove only the folders the installer created, when they are empty."""
    mpath = project / ".trust-kitchen" / "install.json"
    if not mpath.exists():
        return {"removed": 0, "kept": [], "note": "nothing installed"}
    m = _load_manifest(mpath)
    hashes = m.get("hashes", {})
    removed, kept = 0, []
    for rel in m.get("files", []):
        p = project / rel
        if not p.is_file():
            continue
        if rel in hashes and _sha(p) != hashes[rel]:
            kept.append(rel)  # the user changed it after install: not ours to delete
            continue
        p.unlink()
        removed += 1
    for rel in m.get("blocks", []):
        _drop_block(project / rel)
        p = project / rel
        if rel in m.get("created_blocks", []) and p.is_file():
            rest = re.sub(r"^---\r?\n.*?\r?\n---\r?\n", "", _read_keep_eol(p), count=1, flags=re.S)
            if not rest.strip():  # we created it and only our front matter is left
                p.unlink()
    mpath.unlink()
    if "created_dirs" in m:
        dirs = [project / d for d in m["created_dirs"]]
    else:  # manifests written before 2026-11-21: best effort, as before
        dirs = list({(project / r).parent for r in m.get("files", []) + m.get("blocks", [])} | {mpath.parent})
    for d in sorted(dirs, key=lambda x: len(x.parts), reverse=True):
        if d != project and d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return {"removed": removed, "kept": kept}


def status(project: Path) -> Dict[str, Any]:
    mpath = project / ".trust-kitchen" / "install.json"
    if not mpath.exists():
        return {"installed": False}
    m = _load_manifest(mpath)
    skills = {Path(f).parts[-2] for f in m.get("files", []) if f.endswith("/SKILL.md")}
    return {"installed": True, "version": m.get("version"), "agents": m.get("agents", []), "skills": len(skills),
            "files": len(m.get("files", []))}


def _parse_agents(raw: str, names: List[str]) -> List[str]:
    """WHAT: "1,3" or "claude-code, codex" → agent ids; raises ValueError on anything it cannot map."""
    out = []
    for part in (p.strip() for p in raw.split(",") if p.strip()):
        if part.isdigit():
            i = int(part)
            if not 1 <= i <= len(names):
                raise ValueError(f"no agent number {i}; choose 1-{len(names)}")
            out.append(names[i - 1])
        else:
            out.append(part)
    return out


def _ask_agents(t: Dict[str, Any]) -> List[str]:
    names = list(t["agents"])
    for i, n in enumerate(names, 1):
        print(f"  {i:>2}. {t['agents'][n]['label']:<20} ({n})")
    try:
        raw = input("Which agents? numbers or names, comma-separated [1]: ").strip() or "1"
    except EOFError:
        raise ValueError("no terminal to ask in: use --agents claude-code,codex (see: list)") from None
    return _parse_agents(raw, names)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="trust-kitchen", description="Trust Kitchen installer")
    ap.add_argument("command", choices=["install", "update", "uninstall", "status", "list"])
    ap.add_argument("--agents", help="comma-separated names or numbers, e.g. claude-code,codex or 1,2")
    ap.add_argument("--dir", type=Path, default=Path.cwd(), help="project directory (default: current)")
    ap.add_argument("--yes", action="store_true", help="no questions")
    a = ap.parse_args(argv)
    t = _targets(HERE.parent)
    try:
        if a.command == "list":
            for i, (n, s) in enumerate(t["agents"].items(), 1):
                print(f"{i:>2}. {n:<12} {s['label']}")
            return 0
        if a.command == "status":
            print(json.dumps(status(a.dir), indent=2))
            return 0
        if a.command == "uninstall":
            print(json.dumps(uninstall(a.dir), indent=2))
            return 0
        if a.command == "update" and not a.agents:
            st = status(a.dir)
            if not st["installed"]:
                print("Nothing installed here. Run: install")
                return 1
            agents = st["agents"]
        elif a.agents:
            agents = _parse_agents(a.agents, list(t["agents"]))
        elif a.yes:
            raise ValueError("no agents given: use --agents claude-code,codex (see: list)")
        else:
            agents = _ask_agents(t)
        rep = install(a.dir, agents)
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"Trust Kitchen {t['version']} installed for: {', '.join(rep['agents'])}")
    print(f"  {rep['written']} files - skills in {', '.join(rep['skills_dirs'])}")
    for s in rep["skipped"]:
        print(f"  skipped {s}: yours (or changed by you), not overwritten")
    print("Next: open your agent in this project and type /tk (first time: /tk setup).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
