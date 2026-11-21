#!/usr/bin/env python3
"""Skill supply-chain tripwire: flags risky instructions and code in a third-party skill / plugin folder.

WHAT:       Scans every text file of a skill folder for pipe-to-shell installs, reads of secrets and credentials,
            data exfiltration, obfuscated execution, hidden / bidirectional unicode, and prompt-injection phrases.
WHY:        A skill is code that runs with your agent's permissions. Read it before you install it; this script
            points your reading at the lines that matter.
RUNS WHEN:  tk-skill-supply-chain: `python scripts/skill_scan.py path/to/skill-or-plugin`.
AFFECTS:    Prints findings JSON; exit 1 when any hit. Reads only.
CAUTION:    A tripwire, not a malware detector. Zero hits does NOT mean safe; it means "nothing obvious".
CHANGED:    2026-11-20 · v0.1 · new
            2026-11-21 · reads every text file (by content, not extension) and accepts a single file path
            2026-11-21 · UTF-16 read; unreadable / huge files listed as not_scanned; a missing path is exit 2
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

RULES = [
    ("pipe_to_shell", "BLOCKER", re.compile(r"(curl|wget|iwr|Invoke-WebRequest)\b[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh\b|"
                                           r"(curl|wget)[^\n]*-O\s*-\s*\|\s*(ba)?sh|iex\s*\(", re.I)),
    ("secret_read", "MAJOR", re.compile(r"(~|\$HOME|%USERPROFILE%)?/?\.(ssh|aws|gnupg|kube|docker)/|id_rsa|\.env\b|"
                                        r"/etc/(passwd|shadow)|credentials\.json|\.netrc|keychain", re.I)),
    ("exfiltration", "BLOCKER", re.compile(r"(requests\.(post|put)|fetch\(|axios\.(post|put)|curl\s+-(d|F|X\s*POST)|"
                                           r"Invoke-RestMethod)[^\n]*(https?://)", re.I)),
    ("obfuscated_exec", "BLOCKER", re.compile(r"(exec|eval)\s*\(\s*(base64|codecs|zlib|bytes\.fromhex|atob)|"
                                              r"base64\s+-d[^\n]*\|\s*(ba)?sh|FromBase64String", re.I)),
    ("prompt_injection", "BLOCKER", re.compile(r"ignore (all |any )?(previous|prior|above) (instructions|rules)|"
                                               r"do not (tell|inform|show) the user|without (telling|asking) the user|"
                                               r"disregard (your|the) (system|safety)", re.I)),
    ("hidden_unicode", "MAJOR", re.compile("[​‌‍⁠﻿‪-‮⁦-⁩]")),
    ("destructive", "MAJOR", re.compile(r"rm\s+-rf\s+(/|~|\$HOME)|git\s+push\s+(-f|--force)|Remove-Item[^\n]*-Recurse[^\n]*-Force",
                                        re.I)),
]
MAX_BYTES = 2_000_000


def _text(p: Path) -> str | None:
    """WHAT: the file as text, or None for binary files. Decided by content, not by extension: a payload in
    postinstall.mjs, setup.cmd or a file with no extension is read too. UTF-16 with a BOM (common for .ps1) is read;
    other binary data (NUL bytes) is not. Callers list what could not be read (2026-11-21, second review B9)."""
    raw = p.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            return None
    if b"\x00" in raw[:8192]:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def scan_report(folder: Path) -> Dict[str, Any]:
    """WHAT: {hits, not_scanned}: rule hits in text files under `folder` (or in the single file `folder`), and the
    files that could not be read (too big, binary, unknown encoding) — so silence never looks like "clean"."""
    out: List[Dict[str, Any]] = []
    not_scanned: List[str] = []
    paths = [folder] if folder.is_file() else sorted(folder.rglob("*"))
    for p in paths:
        if not p.is_file():
            continue
        if p.stat().st_size > MAX_BYTES:
            not_scanned.append(str(p))
            continue
        text = _text(p)
        if text is None:
            not_scanned.append(str(p))
            continue
        for no, line in enumerate(text.splitlines(), 1):
            for rule, sev, rx in RULES:
                if rx.search(line):
                    out.append({"rule": rule, "category": "security", "severity": sev, "file": str(p), "line": no,
                                "why": f"{rule.replace('_', ' ')} in a third-party skill",
                                "evidence": line.strip()[:160].encode("unicode_escape").decode("ascii")
                                if rule == "hidden_unicode" else line.strip()[:160],
                                "confidence": 4, "fix": "Read this line; do not install until it is explained.",
                                "encode": None})
    return {"hits": out, "not_scanned": not_scanned}


def scan(folder: Path) -> List[Dict[str, Any]]:
    """WHAT: the rule hits only (see scan_report for the files that could not be read)."""
    return scan_report(folder)["hits"]


def main(argv: List[str] | None = None) -> int:
    """WHAT: CLI. Exit 0 no hits · 1 hits found · 2 bad path or usage (nothing was scanned: never read it as clean)."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: skill_scan.py <skill-or-plugin-folder-or-file>", file=sys.stderr)
        return 2
    target = Path(args[0])
    if not target.exists():
        print(f"skill_scan: {target} does not exist: nothing was scanned", file=sys.stderr)
        return 2
    rep = scan_report(target)
    print(json.dumps({**rep, "note": "tripwire only: no hits does not mean safe; read the not_scanned files yourself"},
                     indent=2, ensure_ascii=False))
    return 1 if rep["hits"] else 0


if __name__ == "__main__":
    sys.exit(main())
