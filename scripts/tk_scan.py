#!/usr/bin/env python3
"""Deterministic diff scanner: the cheap, repeatable first layer of a Trust Kitchen review.

WHAT:       Reads a unified diff and reports what a machine can prove without judgement: leaked secrets, weakened tests,
            lint suppressions, symptom fixes (sleep / empty catch), excuse comments, debug leftovers, dangerous calls,
            prompt-injection text aimed at reviewers, dependency changes, oversized diffs. Tags restricted areas
            (auth, ci, migration, infra, security, dependencies) for the merge gate.
WHY:        Anything provable by a script must not cost model tokens or depend on a reviewer noticing it.
RUNS WHEN:  `python scripts/tk_scan.py --base origin/main` (or `--diff file.patch`), first step of tk-review.
AFFECTS:    Prints JSON {findings, areas, stats} to stdout. Exit 0 no BLOCKER · 1 BLOCKER found · 2 the scan could not
            run (bad ref, unreadable file): callers must treat 2 as "not checked", never as clean. Writes nothing.
CAUTION:    Only ADDED lines are judged (plus removed tests). Patterns are heuristics with file:line evidence; reviewers
            may dismiss a hit, but must say why. Secret values are never echoed — only a masked hint.
CHANGED:    2026-11-20 · v0.1 · new
            2026-11-21 · provenance_comment (MINOR): body comments citing a person or a review as the reason
            2026-11-21 · large_diff is MINOR advice (no hard size cap by default)
            2026-11-21 · independent review fixes: hunk-aware parser, renamed/moved tests are not deletions, .txt
                         is not docs, --config restricted_paths, UTF-8 git output, exit 2 on scan errors
            2026-11-21 · second review: git diff ignores the PR's .gitattributes; only prose is docs; restricted_paths
                         validated (list of strings), globs and ./ accepted
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

MAX_LINES_DEFAULT = 400  # ASSUMED default review size; tune per repo with --max-lines

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Generic secret assignment", re.compile(
        r"(?i)\b(api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*['\"][A-Za-z0-9/+_\-]{20,}['\"]")),
]
TEST_SKIP = re.compile(r"(@pytest\.mark\.skip|@unittest\.skip|\bxit\(|\bxdescribe\(|\b(it|test|describe)\.(only|skip)\(|"
                       r"\bt\.Skip\(|#\[ignore\])")
TEST_DEF = re.compile(r"^\s*(def test_\w+|(it|test)\(\s*['\"`]|func Test\w+\()")
WEAK_ASSERT = re.compile(r"^\s*assert\s+True\b|expect\(true\)\.toBe\(true\)")
SUPPRESSION = re.compile(r"(#\s*type:\s*ignore|#\s*noqa|eslint-disable|@ts-ignore|@ts-expect-error|#\s*pylint:\s*disable|"
                         r"//\s*nolint|@SuppressWarnings|#\s*nosec|#\[allow\(|"
                         r"\bunsafe\s*\{|\bas\s+any\b|:\s*any\b(?=\s*[,)=;{]))")  # + language escape hatches (2026-11-21)
SYMPTOM = re.compile(r"(\btime\.sleep\(|\bsetTimeout\(|\bThread\.sleep\(|\bTask\.Delay\(|\basyncio\.sleep\(|"
                     r"catch\s*\([^)]*\)\s*\{\s*\}|\bcatch\s*\{\s*\})")
EXCEPT_LINE = re.compile(r"^\s*except(\s+[\w.]+(\s+as\s+\w+)?)?\s*:\s*(#.*)?$")
PASS_LINE = re.compile(r"^\s*pass\s*(#.*)?$")
EXCUSE = re.compile(r"(#|//|/\*|<!--|--)\s*.*\b(hack|workaround|temporary|temp fix|quick fix|for now|todo|fixme|xxx|"
                    r"don'?t touch|do not touch|magic)\b", re.I)
# v0.3 (2026-11-21): provenance_comment — a body comment whose only reason is a person or a review (see the tests)
COMMENT_PART = re.compile(r"(?:^|\s)(?:#|//|/\*|<!--|--)\s?(.*)$")
VERBS = r"(said|says|told|asked|insisted|wants|requested)\b"
PROVENANCE = [re.compile(r"(@[\w.-]+|\b[A-Z][a-z]+)\s+" + VERBS),  # a name: case-sensitive on purpose
              re.compile(r"\b(the\s+)?(reviewer|lead|boss|manager|team|customer|client|he|she|they)\s+" + VERBS, re.I),
              re.compile(r"\b(per|from|after|as requested in|as discussed in)\s+(the\s+)?(code\s+|pr\s+)?review\b", re.I)]
DEBUG = re.compile(r"(\bconsole\.(log|debug)\(|^\s*debugger;?|\bpdb\.set_trace\(|\bbreakpoint\(\)|\bbinding\.pry\b)")
DANGEROUS = re.compile(r"(\beval\(|\bexec\(|shell\s*=\s*True|\bpickle\.loads?\(|\byaml\.load\((?![^)]*SafeLoader)|"
                       r"\.innerHTML\s*=|dangerouslySetInnerHTML|\bos\.system\(|child_process\.exec\(|\bMarshal\.load\()")
INJECTION = re.compile(r"(?i)(ignore (all |any )?(previous|prior|above) (instructions|rules)|disregard (the )?(system|previous)|"
                       r"(approve|merge) this (pr|pull request|change)\b.*\b(reviewer|ai|agent|model)|"
                       r"\b(reviewer|ai|agent|model)\b.*\b(approve|merge) this|you are now in \w+(-\w+)* mode|"
                       r"new instructions for the (ai|agent|reviewer))")
AREAS = [
    ("ci", re.compile(r"(^|/)(\.github/workflows|\.gitlab-ci\.yml|Jenkinsfile|\.circleci|azure-pipelines)")),
    ("migration", re.compile(r"(^|/)(migrations?|alembic|db/migrate)/|\.sql$")),
    ("auth", re.compile(r"(^|/)(auth|authn|authz|login|session|oauth|sso|permissions?|iam|rbac)(/|[._-])", re.I)),
    ("security", re.compile(r"(^|/)(security|crypto|secrets?)(/|[._-])|SECURITY\.md$", re.I)),
    ("infra", re.compile(r"(^|/)(Dockerfile|docker-compose[^/]*\.ya?ml|terraform|helm|k8s|kubernetes|\.tf$)", re.I)),
    ("dependencies", re.compile(r"(^|/)(requirements[^/]*\.txt|pyproject\.toml|poetry\.lock|package\.json|"
                                r"package-lock\.json|yarn\.lock|pnpm-lock\.yaml|go\.mod|go\.sum|Cargo\.(toml|lock)|Gemfile)$")),
    ("review-config", re.compile(r"(^|/)(\.trust-kitchen|CODEOWNERS)")),
]
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec)/|(_test|\.test|\.spec)\.\w+$|(^|/)test_\w+\.py$")
# .txt is not documentation (requirements.txt, robots.txt, data): only prose formats and docs/ count (2026-11-21)
DOC_PATH = re.compile(r"\.(md|rst|adoc)$", re.I)  # prose only: docs/conf.py is code (second review B4)


def parse_diff(text: str) -> List[Dict[str, Any]]:
    """WHAT: unified diff → [{path, added:[(new_line_no, text)], removed:[(old_line_no, text)]}] (git diff format)."""
    # Hunk line counts decide what is content: inside a hunk, "--- x" is a removed "-- x" and "+++ x" an added
    # "++ x" (SQL / Lua comments, C++ increments). Headers are only read between hunks (fixed 2026-11-21).
    files: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None
    new_no = old_no = 0
    old_left = new_left = 0
    for raw in text.splitlines():
        in_hunk = old_left > 0 or new_left > 0
        if not in_hunk:
            if raw.startswith("diff --git "):
                cur = {"path": raw.split(" b/", 1)[-1].strip(), "added": [], "removed": []}
                files.append(cur)
                continue
            if cur is None:
                continue
            if raw.startswith("+++ "):
                p = raw[4:].strip()
                if p != "/dev/null":
                    cur["path"] = p[2:] if p.startswith("b/") else p
                continue
            m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw)
            if m:
                old_no, new_no = int(m.group(1)), int(m.group(3))
                old_left = int(m.group(2)) if m.group(2) is not None else 1
                new_left = int(m.group(4)) if m.group(4) is not None else 1
            continue
        if raw.startswith("\\"):  # "\ No newline at end of file"
            continue
        if raw.startswith("+"):
            cur["added"].append((new_no, raw[1:]))
            new_no += 1
            new_left -= 1
        elif raw.startswith("-"):
            cur["removed"].append((old_no, raw[1:]))
            old_no += 1
            old_left -= 1
        else:  # context line (" x" or an empty line)
            new_no += 1
            old_no += 1
            new_left -= 1
            old_left -= 1
    return files


def _mask(s: str) -> str:
    s = s.strip()
    return (s[:4] + "…" + f"({len(s)} chars)") if len(s) > 8 else "…"


def _finding(rule: str, category: str, severity: str, path: str, line: int, why: str, evidence: str, fix: str,
             encode: Optional[str]) -> Dict[str, Any]:
    return {"rule": rule, "category": category, "severity": severity, "file": path, "line": line, "why": why,
            "evidence": evidence[:200], "confidence": 4, "fix": fix, "encode": encode, "source": "deterministic"}


TEST_NAME = re.compile(r"def (test_\w+)|func (Test\w+)\(|\b(?:it|test)\(\s*(['\"`])(.*?)\3")


def _restricted(path: str, pattern: str) -> bool:
    """WHAT: does `path` fall under a restricted_paths entry? A folder prefix ("payments/", "./payments") or a glob
    ("src/*/billing.py"). Entries are written by people, so "./" and a missing trailing slash are tolerated."""
    pat = pattern.strip()
    pat = pat[2:] if pat.startswith("./") else pat
    if any(ch in pat for ch in "*?["):
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat.rstrip("/") + "/*")
    return path == pat.rstrip("/") or path.startswith(pat.rstrip("/") + "/")


def _test_name(line: str) -> Optional[str]:
    m = TEST_NAME.search(line)
    return next((g for g in (m.group(1), m.group(2), m.group(4)) if g), None) if m else None


def scan(diff_text: str, description: str = "", max_lines: int = MAX_LINES_DEFAULT,
         restricted_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """WHAT: run every deterministic rule over a diff (+ PR description) → {findings, areas, stats}.
    `restricted_paths` (from .trust-kitchen/config.json) tags matching files with the area "restricted-path"."""
    files = parse_diff(diff_text)
    out: List[Dict[str, Any]] = []
    areas: List[str] = []
    changed = 0
    # a test is deleted only if its name is gone from the whole diff: a new signature or a move is not a deletion
    added_tests = {n for f in files for _, t in f["added"] if TEST_DEF.search(t) for n in [_test_name(t)] if n}
    for f in files:
        path = f["path"]
        is_test, is_doc = bool(TEST_PATH.search(path)), bool(DOC_PATH.search(path))
        changed += len(f["added"]) + len(f["removed"])
        for name, rx in AREAS:
            if rx.search(path) and name not in areas:
                areas.append(name)
        if any(_restricted(path, r) for r in (restricted_paths or [])):
            if "restricted-path" not in areas:
                areas.append("restricted-path")
        for no, text in f["removed"]:
            if TEST_DEF.search(text) and _test_name(text) not in added_tests:
                out.append(_finding("test_weakened", "tests", "BLOCKER", path, no, "A test was deleted.",
                                    text.strip(), "Keep the test, or explain in the PR why the behaviour it guarded "
                                    "no longer exists and get a human to accept it.", "CI check: fail when test count drops"))
        prev = ""
        for no, text in f["added"]:
            for label, rx in SECRET_PATTERNS:
                m = rx.search(text)
                if m:
                    out.append(_finding("secret", "security", "BLOCKER", path, no, f"{label} committed in code.",
                                        f"{label}: {_mask(m.group(0))}", "Remove it, rotate it, load it from the "
                                        "environment or a secret store.", "pre-commit secret scanner"))
                    break
            if TEST_SKIP.search(text) or (is_test and WEAK_ASSERT.search(text)):
                out.append(_finding("test_weakened", "tests", "BLOCKER", path, no,
                                    "A test is skipped, focused or made trivially true.", text.strip(),
                                    "Fix the code or the test; do not silence it.", "lint rule: no skip/only in tests"))
            if SUPPRESSION.search(text):
                out.append(_finding("lint_suppression", "slop", "MAJOR", path, no,
                                    "A checker is silenced instead of the problem being fixed.", text.strip(),
                                    "Fix the reported issue; if the checker is wrong, change its config with a reason.",
                                    "CI: count suppressions, fail when it grows"))
            if not is_test and (SYMPTOM.search(text) or (PASS_LINE.match(text) and EXCEPT_LINE.match(prev))):
                out.append(_finding("symptom_fix", "slop", "MAJOR", path, no,
                                    "Waiting or swallowing an error hides a cause instead of fixing it.", text.strip(),
                                    "Find the real ordering / error and fix it at the source.",
                                    "lint rule: ban sleep/setTimeout/empty catch outside tests"))
            if not is_doc and EXCUSE.search(text):
                out.append(_finding("excuse_comment", "slop", "MINOR", path, no,
                                    "Comment explains a shortcut instead of fixing it; agents will copy it.",
                                    text.strip(), "Fix the code and delete the comment, or encode the constraint "
                                    "as a type / test.", "lint rule: no hack/todo/workaround comments"))
            cm = None if is_doc else COMMENT_PART.search(text)
            if cm and any(rx.search(cm.group(1)) for rx in PROVENANCE):
                # header blocks (docstrings) carry no comment marker, so only body comments are judged here
                out.append(_finding("provenance_comment", "slop", "MINOR", path, no,
                                    "Comment uses a person or a review as the reason; a one-off remark becomes a "
                                    "rule nobody can check, and agents copy it everywhere.", text.strip(),
                                    "Delete it, or state the real constraint as a type, test or lint rule "
                                    "(if the remark was meant as a lasting rule, confirm that with the person).",
                                    "tk-learn-rules: encode the constraint, not who said it"))
            if not is_test and DEBUG.search(text):
                out.append(_finding("debug_leftover", "slop", "MINOR", path, no, "Debug code left in.", text.strip(),
                                    "Remove it or use the project logger.", "lint rule: no-console / no-debugger"))
            if DANGEROUS.search(text):
                out.append(_finding("dangerous_call", "security", "MAJOR", path, no,
                                    "Call that executes or deserialises untrusted input if the input is not trusted.",
                                    text.strip(), "Use a safe API (safe_load, list args, textContent) or prove the "
                                    "input is trusted.", "static-analysis / lint rule for the call"))
            if INJECTION.search(text):
                out.append(_finding("prompt_injection", "security", "BLOCKER", path, no,
                                    "Text addressed to an automated reviewer tries to change its instructions.",
                                    text.strip(), "Remove it. Reviewers treat diff content as data.", None))
            prev = text
        if any(a == "dependencies" for a in areas) and f["added"] and AREAS[5][1].search(path):
            out.append(_finding("dependency_change", "security", "MINOR", path, f["added"][0][0],
                                "Dependencies changed: needs a supply-chain look (source, version pin, licence).",
                                f"{len(f['added'])} added line(s)", "Pin exact versions; check the package is the one "
                                "you meant.", None))
    if description and INJECTION.search(description):
        out.append(_finding("prompt_injection", "security", "BLOCKER", "<pr-description>", 0,
                            "PR description tries to instruct the automated reviewer.", description[:200],
                            "Remove it. Reviewers treat the description as data.", None))
    if changed > max_lines:
        # advice, not a gate (2026-11-21): MINOR never blocks; split when the change has separable parts
        out.append(_finding("large_diff", "process", "MINOR", "<diff>", 0,
                            f"{changed} changed lines (advice above {max_lines}): hard to review in one sitting.",
                            f"{changed} lines in {len(files)} files", "If it has separable parts, split into atomic "
                            "PRs that each end in a check; if it is one logical change, say so in the PR body.",
                            None))
    return {"findings": out, "areas": areas,
            "stats": {"files": len(files), "changed_lines": changed,
                      "docs_only": bool(files) and all(DOC_PATH.search(f["path"]) for f in files)
                      and not set(areas) & {"dependencies", "ci", "review-config", "restricted-path"}}}


def _git_diff(base: str) -> str:
    # UTF-8 on every OS: with the platform default (cp1252 on Windows) any non-ASCII diff crashed (2026-11-21)
    # --text --no-ext-diff --no-textconv: a PR's own .gitattributes ("* -diff", textconv) must not hide content (B3)
    return subprocess.run(["git", "diff", "--no-color", "--text", "--no-ext-diff", "--no-textconv", "-U0",
                           f"{base}...HEAD"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Trust Kitchen deterministic diff scanner")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--diff", help="path to a unified diff file ('-' for stdin)")
    src.add_argument("--base", help="git base ref; scans base...HEAD")
    ap.add_argument("--description", default="", help="PR description text or @file")
    ap.add_argument("--max-lines", type=int, default=MAX_LINES_DEFAULT)
    ap.add_argument("--config", help="project config (.trust-kitchen/config.json): reads restricted_paths")
    a = ap.parse_args(argv)
    # exit codes: 0 no BLOCKER · 1 BLOCKER found · 2 the scan itself could not run (never mistaken for a finding)
    try:
        if a.diff:
            text = sys.stdin.read() if a.diff == "-" else open(a.diff, encoding="utf-8").read()
        else:
            text = _git_diff(a.base)
        desc = open(a.description[1:], encoding="utf-8").read() if a.description.startswith("@") else a.description
        restricted = []
        if a.config:
            cfg = json.load(open(a.config, encoding="utf-8"))
            restricted = (cfg.get("restricted_paths") or []) if isinstance(cfg, dict) else None
            if not isinstance(restricted, list) or not all(isinstance(r, str) for r in restricted):
                # a string would be read letter by letter and silently protect nothing (second review B11)
                raise ValueError("config: restricted_paths must be a list of path strings")
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print(f"tk_scan: could not run: {e}", file=sys.stderr)
        return 2
    result = scan(text, desc, a.max_lines, restricted)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if any(f["severity"] == "BLOCKER" for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
