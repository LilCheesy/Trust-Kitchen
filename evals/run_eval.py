#!/usr/bin/env python3
"""Eval runner: measures how well each skill does its job on cases whose expectations were written first.

WHAT:       Loads evals/cases/*/case.json. Three layers:
            - deterministic: scored live by running tk_scan on the case's diff.patch;
            - review: scored from a reviewer's result file (results/<id>.json with "findings");
            - skill: any other skill, scored from a judge's rubric file (results/<id>.json with "rubric": {item: bool}).
            A case without a result is NOT RUN, never a miss. Clean cases measure false alarms (a proven BLOCKER/MAJOR).
            Extras: `split` (tune / holdout) scores the two sets apart; `prepare_blind` copies the inputs under neutral
            names so the agent cannot tell it is being measured; `second_dir` compares a second judge (ideally another
            model) and lists the cases where the two disagree as unstable.
WHY:        A skill is a process you can measure, like code with unit tests: run its cases on every change. Tune on one
            set until it is perfect; the holdout set, never looked at while tuning, is the honest number.
RUNS WHEN:  `python evals/run_eval.py [--results DIR] [--second DIR] [--key key.json] [--split tune|holdout]`
            and `python evals/run_eval.py blind OUT_DIR [--seed S]`; .github/workflows/selfcheck.yml runs both splits.
AFFECTS:    Prints a JSON report; exit 1 when a measured rate misses its target. `blind` writes OUT_DIR/work/* and
            OUT_DIR/key.json only.
CAUTION:    Targets are ASSUMED defaults. NOT RUN is null, not 0. Give the agent OUT_DIR/work only, never key.json or
            the cases folder. A perfect holdout score is still a reason to look twice at how it was produced.
CHANGED:    2026-11-20 · v0.1 · new
            2026-11-21 · holdout split, blind copies, second judge, rubric-scored cases for any skill
            2026-11-21 · an empty selection FAILs; skill cases get no duplicate request.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import tk_scan  # noqa: E402
from merge_gate import confidence  # noqa: E402

BLOCKING = {"BLOCKER", "MAJOR"}


def load_cases(cases_dir: Path, split: Optional[str] = None) -> List[Dict[str, Any]]:
    """WHAT: every case, optionally only one split ("tune" is the default split of a case)."""
    out = []
    for cj in sorted(cases_dir.glob("*/case.json")):
        c = json.loads(cj.read_text(encoding="utf-8"))
        c["_dir"] = cj.parent
        if split in (None, "all") or c.get("split", "tune") == split:
            out.append(c)
    return out


def _matches(f: Dict[str, Any], exp: Dict[str, Any]) -> bool:
    if "rule" in exp and f.get("rule") != exp["rule"]:
        return False
    if "category" in exp and f.get("category") != exp["category"]:
        return False
    return not exp.get("file") or str(f.get("file", "")).endswith(exp["file"])


def _proven(f: Dict[str, Any]) -> bool:
    return confidence(f.get("confidence")) >= 3  # same rule as the gate: "high" or missing is unproven, not a crash


def _rate(num: int, den: int) -> Optional[float]:
    return round(num / den, 4) if den else None


def _load_result(results_dir: Optional[Path], cid: str, key: Optional[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """WHAT: the result for case `cid`, stored under its own id or under its blind name (via `key`)."""
    if not results_dir:
        return None
    names = [cid] + [blind for blind, real in (key or {}).items() if real == cid]
    for n in names:
        p = results_dir / f"{n}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return None


def _outcome(c: Dict[str, Any], res: Optional[Dict[str, Any]], det_findings: List[Dict[str, Any]]) -> Optional[str]:
    """WHAT: one comparable verdict per case for the stability check (None = not run)."""
    if res is None:
        return None
    if c["layer"] == "skill":
        rub = res.get("rubric", {})
        return ",".join(f"{e['id']}={bool(rub.get(e['id']))}" for e in c["expect"])
    fs = res.get("findings", [])
    if c.get("clean"):
        return f"alarm={any(f.get('severity') in BLOCKING and _proven(f) for f in fs)}"
    pool = fs + det_findings
    return ",".join(str(any(_matches(f, e) and _proven(f) for f in pool)) for e in c["expect"])


def evaluate(cases_dir: Path, results_dir: Optional[Path] = None, split: Optional[str] = None,
             key: Optional[Dict[str, str]] = None, second_dir: Optional[Path] = None) -> Dict[str, Any]:
    """WHAT: the full report: per layer, per skill, clean-case false alarms, and judge stability."""
    cases = load_cases(cases_dir, split)
    det = {"expected": 0, "caught": 0, "missed": []}
    rev = {"expected": 0, "caught": 0, "missed": [], "not_run": 0}
    clean = {"cases": 0, "false_alarms": 0, "judged": 0, "deterministic_false_alarms": 0, "alarms": []}
    skills: Dict[str, Dict[str, Any]] = {}
    stab = {"compared": 0, "agree": 0, "unstable": []}
    for c in cases:
        res = _load_result(results_dir, c["id"], key)
        det_findings: List[Dict[str, Any]] = []
        if c["layer"] != "skill":
            diff = (c["_dir"] / "diff.patch").read_text(encoding="utf-8")
            det_findings = tk_scan.scan(diff, c.get("description", ""))["findings"]
        if second_dir is not None:
            o1, o2 = _outcome(c, res, det_findings), _outcome(c, _load_result(second_dir, c["id"], key), det_findings)
            if o1 is not None and o2 is not None:
                stab["compared"] += 1
                if o1 == o2:
                    stab["agree"] += 1
                else:
                    stab["unstable"].append(c["id"])
        if c["layer"] == "skill":
            s = skills.setdefault(c["skill"], {"expected": 0, "passed": 0, "failed": [], "not_run": 0})
            if res is None:
                s["not_run"] += 1
                continue
            rub = res.get("rubric", {})
            for e in c["expect"]:
                s["expected"] += 1
                if rub.get(e["id"]) is True:
                    s["passed"] += 1
                else:
                    s["failed"].append(f"{c['id']}: {e['id']}")
            continue
        rev_findings = None if res is None else res.get("findings", [])
        if c.get("clean"):
            clean["cases"] += 1
            if any(f["severity"] in BLOCKING for f in det_findings):
                clean["deterministic_false_alarms"] += 1
                clean["alarms"].append(f"{c['id']} (deterministic)")
            if rev_findings is not None:
                clean["judged"] += 1
                if any(f.get("severity") in BLOCKING and _proven(f) for f in rev_findings):
                    clean["false_alarms"] += 1
                    clean["alarms"].append(f"{c['id']} (review)")
            continue
        if c["layer"] == "deterministic":
            for exp in c["expect"]:
                det["expected"] += 1
                if any(_matches(f, exp) for f in det_findings):
                    det["caught"] += 1
                else:
                    det["missed"].append(f"{c['id']}: {exp}")
        else:
            if rev_findings is None:
                rev["not_run"] += 1
                continue
            pool = rev_findings + det_findings
            for exp in c["expect"]:
                rev["expected"] += 1
                if any(_matches(f, exp) and _proven(f) for f in pool):
                    rev["caught"] += 1
                else:
                    rev["missed"].append(f"{c['id']}: {exp}")
    det["catch_rate"] = _rate(det["caught"], det["expected"])
    rev["catch_rate"] = _rate(rev["caught"], rev["expected"])
    clean["false_alarm_rate"] = _rate(clean["false_alarms"], clean["judged"])
    for s in skills.values():
        s["pass_rate"] = _rate(s["passed"], s["expected"])
    out: Dict[str, Any] = {"cases": len(cases), "split": split or "all", "deterministic": det, "review": rev,
                           "clean": clean, "skills": skills}
    if second_dir is not None:
        out["stability"] = stab
    return out


def prepare_blind(cases_dir: Path, out_dir: Path, seed: str = "") -> Dict[str, str]:
    """WHAT:       copy each case's input to OUT/work/<neutral name>/ (change.patch or task.md, plus request.md) and
                   write OUT/key.json {neutral name: case id}; returns the key.
    WHY:           An agent that can tell it is being measured behaves differently: no case id, layer, expectation or
                   "eval" / "test" word may reach it.
    CAUTION:       Neutral names come from a hash of seed + id; use a new seed per run so names are not learned."""
    work = out_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    key: Dict[str, str] = {}
    for c in load_cases(cases_dir):
        name = "item-" + hashlib.sha256(f"{seed}:{c['id']}".encode("utf-8")).hexdigest()[:8]
        d = work / name
        d.mkdir()
        src = c["_dir"]
        if (src / "diff.patch").exists():
            shutil.copyfile(src / "diff.patch", d / "change.patch")
        if (src / "task.md").exists():
            shutil.copyfile(src / "task.md", d / "task.md")
        if c.get("description") and not (src / "task.md").exists():  # a skill case's task already says it all
            (d / "request.md").write_text(c["description"] + "\n", encoding="utf-8")
        key[name] = c["id"]
    (out_dir / "key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    return key


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cases_default = Path(__file__).resolve().parent / "cases"
    if argv[:1] == ["blind"]:
        bp = argparse.ArgumentParser(description="Trust Kitchen eval: blind copies")
        bp.add_argument("out", type=Path)
        bp.add_argument("--cases", type=Path, default=cases_default)
        bp.add_argument("--seed", default="")
        b = bp.parse_args(argv[1:])
        key = prepare_blind(b.cases, b.out, b.seed)
        print(f"{len(key)} item(s) in {b.out / 'work'}; key in {b.out / 'key.json'} (never give it to the agent)")
        return 0
    ap = argparse.ArgumentParser(description="Trust Kitchen eval runner")
    ap.add_argument("--cases", type=Path, default=cases_default)
    ap.add_argument("--results", type=Path, help="folder with <case-id or blind name>.json results")
    ap.add_argument("--second", type=Path, help="results of a second judge (another model): reports stability")
    ap.add_argument("--key", type=Path, help="key.json from `blind`, to read results stored under blind names")
    ap.add_argument("--split", choices=["tune", "holdout", "all"], default="all")
    ap.add_argument("--min-catch", type=float, default=0.8)
    ap.add_argument("--max-false", type=float, default=0.1)
    a = ap.parse_args(argv)
    key = json.loads(a.key.read_text(encoding="utf-8")) if a.key else None
    r = evaluate(a.cases, a.results, a.split, key, a.second)
    fails = []
    if r["cases"] == 0:  # an empty selection measures nothing; it must never read as PASS (2026-11-21)
        fails.append(f"no cases in split '{a.split}' under {a.cases}")
    for layer in ("deterministic", "review"):
        rate = r[layer]["catch_rate"]
        if rate is not None and rate < a.min_catch:
            fails.append(f"{layer} catch rate {rate} < {a.min_catch}")
    for name, s in r["skills"].items():
        if s["pass_rate"] is not None and s["pass_rate"] < a.min_catch:
            fails.append(f"{name} pass rate {s['pass_rate']} < {a.min_catch}")
    far = r["clean"]["false_alarm_rate"]
    if far is not None and far > a.max_false:
        fails.append(f"false alarm rate {far} > {a.max_false}")
    if r["clean"]["deterministic_false_alarms"]:
        fails.append(f"deterministic layer raised {r['clean']['deterministic_false_alarms']} false alarm(s) on clean cases")
    if r.get("stability", {}).get("unstable"):
        fails.append(f"judges disagree on {len(r['stability']['unstable'])} case(s): unstable")
    r["targets"] = {"min_catch": a.min_catch, "max_false": a.max_false, "assumed": True}
    r["result"] = "FAIL: " + "; ".join(fails) if fails else "PASS (NOT RUN layers are not scored)"
    print(json.dumps(r, indent=2, ensure_ascii=False, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
