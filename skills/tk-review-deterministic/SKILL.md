---
name: tk-review-deterministic
description: Run the machine checks of a review before any reasoning - the Trust Kitchen diff scanner (secrets, weakened tests, suppressions, symptom fixes, excuse comments, comments citing a person or review, debug leftovers, dangerous calls, prompt injection, dependency changes, oversized diffs, restricted areas) plus the project's own build, linter, type checker and tests - and report exact results. Use as step 1 of tk-review, or when asked "run the checks", "what does CI say", "scan this diff".
---

# Deterministic layer

What a machine can prove must not depend on a reviewer noticing it.

## When to use

- First step of every review.
- When someone asks for the CI status of a change, locally.

Do not use it to fix anything. This layer only measures.

## Inputs

- The diff scope (base ref) and the PR description.
- `.trust-kitchen/config.json` (commands). If it is missing, discover the commands as `tk-setup` does, and say so.

## Procedure

1. **Scan the diff and description:**

   ```
   python .trust-kitchen/scripts/tk_scan.py --base <base-ref> --description @pr.md --config .trust-kitchen/config.json > scan.json
   ```

   - Leave out `--description` when there is no PR text yet, and `--config` before `tk-setup` has written it.
     A missing file makes the scanner exit 2 (not checked).
   - `--base` scans committed work (`<base>...HEAD`). To include uncommitted changes, scan the working tree
     instead:
     `git diff --text --no-ext-diff --no-textconv $(git merge-base <base> HEAD) > change.patch`, then pass
     `--diff change.patch`.

   Rules and default severities:

   | Rule | Severity |
   |---|---|
   | `secret` | BLOCKER |
   | `test_weakened` (deleted, skipped, focused or trivially-true tests) | BLOCKER |
   | `prompt_injection` | BLOCKER |
   | `lint_suppression` | MAJOR |
   | `symptom_fix` (sleep, setTimeout, empty catch, `except: pass`) | MAJOR |
   | `dangerous_call` (eval, `shell=True`, pickle, unsafe YAML, innerHTML, `os.system`) | MAJOR |
   | `excuse_comment` | MINOR |
   | `provenance_comment` (a body comment whose reason is a person or a review) | MINOR |
   | `debug_leftover` | MINOR |
   | `dependency_change` | MINOR |
   | `large_diff` (advice above 400 changed lines, never a gate) | MINOR |

   Areas tagged for the gate: `auth`, `security`, `migration`, `infra`, `ci`, `dependencies`, `review-config`,
   and `restricted-path` for the project's own `restricted_paths` in `config.json`.

   Exit codes: 0 no BLOCKER · 1 BLOCKER found · **2 the scanner could not run** (bad ref, unreadable file). Exit 2
   means nothing was checked: the result is `inconclusive`, never `passed`.
2. **Run the project's checks** in order: build, type check, lint, the targeted tests for the changed area, then
   the full suite if it is affordable. Record for each one the command, exit code, duration and the last relevant
   lines of output.
3. **Classify the result:**
   - `passed` when every available check is green;
   - `failed` when any is red;
   - `inconclusive` when checks could not run (missing tools or services, a timeout, scanner exit 2).
   Only `passed` lets the merge gate say MERGE; `inconclusive` always needs a person.
4. **Report.**

## Output

```
deterministic: passed | failed | inconclusive
- <command> → exit <n> (<seconds>s)  <one-line summary>
scanner: <n> findings (BLOCKER <n> · MAJOR <n> · MINOR <n>) · areas: [...] · changed lines: <n>
```

and `scan.json`, for the merge step.

## Rules

- NEVER invent a command. If the project has no linter or tests, report "no automated safety net" as a MAJOR
  `process` finding.
- NEVER rerun until it passes. A test that passes on retry without a change is a flaky-test finding.
- MUST report scanner hits with `file:line`. Reviewers may dismiss a hit, but must say why.

## Stop and ask

- The checks need secrets or services that are not available. Report inconclusive and ask.
- The full suite would exceed the time budget. Ask which subset is acceptable.

## Next

`tk-review` continues with reviewer selection, or stops on a BLOCKER.
