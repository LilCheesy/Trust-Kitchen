---
name: tk-sec-finding-gate
description: Validate a security finding before it is reported or allowed to block a merge - seven questions (in scope, reachable, attacker-controlled, unprotected, impact, proven, fixable) with REPORT / DOWNGRADE / NEEDS CHAIN / DROP outcomes; downgrades instead of escalating and never exploits further. Use inside tk-review-security, when triaging scanner or bot security alerts, or when asked "is this a real vulnerability", "false positive?", "triage this security finding".
---

# Security finding gate

A wrong security report costs trust. Each finding must answer all seven questions; any open question means a
downgrade.

## When to use

- For every security finding before it is reported.
- When triaging alerts from scanners, dependency bots or other reviewers.

Do not use it to decide on general (non-security) findings. They follow the confidence ladder in `tk-evidence`.

## Inputs

- The candidate finding: location, suspected class and evidence.
- The code around it, and the entry points.

## Procedure

Answer each question with evidence:

| # | Question | Evidence expected |
|---|---|---|
| 1 | **In scope?** Is the vulnerable code part of the change, or directly affected by it? | `file:line` in the diff, or a traced call into changed code |
| 2 | **Reachable?** Does the line run in production (not only in tests, dead code or behind a flag that is always off)? | a call path from a real entry point |
| 3 | **Attacker-controlled?** Does untrusted input reach it, unchanged enough to matter? | the source → sink hops |
| 4 | **Unprotected?** Is no existing control (validation, auth, encoding, framework default) stopping it? | the protections looked for, and why they do not apply |
| 5 | **Impact?** What concretely happens: other users' data, code execution, money, availability? | one sentence + CVSS 3.1 vector |
| 6 | **Proven?** A failing test or sandbox repro, or only reasoning? | command + output (confidence 4–5), else ≤ 3 |
| 7 | **Fixable here?** What is the smallest fix, and how is it encoded so the class cannot return? | fix + encode |

Then pick the outcome:

| Outcome | When | Effect |
|---|---|---|
| **REPORT** | 1–5 answered and 6 at confidence ≥ 3 | may block |
| **DOWNGRADE** | one of 2–4 uncertain | reported as unproven (confidence ≤ 2); does not block; name the open question |
| **NEEDS CHAIN** | impact depends on another weakness that is not present | note both; does not block |
| **DROP** | out of scope, unreachable, or already protected | one-line reason in the "dropped" list |

## Output

One row per finding: `rule · outcome · answers to Q1–Q7 (short) · confidence · cvss`.

## Rules

- NEVER escalate by attacking. Proof happens only in a local sandbox or a unit test with fixtures.
- NEVER inflate severity to get attention. Severity follows impact and reachability.
- MUST redact secrets, tokens and personal data from evidence.

## Stop and ask

- Answering question 2 or 3 needs production logs or data. Ask the owner rather than guessing.

## Next

Back to `tk-review-security`.
