---
name: tk-pr
description: Prepare a pull request a reviewer can trust in one minute - small logical commits, clean diff, and a body that states intent, what changed, evidence, risk, rollback and what was not tested. Use when a change is ready to propose, or when asked "open a PR", "write the PR description", "tidy my commits".
---

# Pull request

A PR is a request to trust you. Make it easy: small, honest, and with the evidence already attached.

## When to use

- A change is built and its checks are green.
- An existing PR is messy (mixed concerns, no description, no evidence).

Do not use it to push or merge. This skill prepares the PR; pushing waits for the owner's go.

## Inputs

- The branch and its commits.
- The plan or spec it implements.
- Evidence from `tk-build` / `tk-review-verify`.

## Procedure

1. **Scope check.** The diff matches the plan. Anything extra goes to its own PR.
2. **Size check.** There is no hard cap. Each PR is **atomic**: one logical change that git history can explain
   and a revert can undo.
   - If the diff has separable parts, split them into a stack of PRs, each ending in a check.
   - If it is one logical change and still large, say so in the body. Above about 400 lines the merge gate adds a
     note, not a block.
3. **Commits.** One logical change per commit. Refactors are separate from behaviour changes. Messages are plain
   and specific: "reject zero quantity in cart API", not "fix stuff".
4. **Self-scan.** Run `python .trust-kitchen/scripts/tk_scan.py --base <default_branch> --description @pr.md`.
   Fix everything it reports about your own change.
5. **Write the body** (template below). Keep it under one screen.
6. **Ask before pushing.** Pushing is outward-facing.

## Output

```markdown
## What and why
<2–3 sentences: the user-visible change and the reason. Link the issue/spec.>

## Changes
- <file or area>: <what changed>

## Evidence
- <command> → <result>      (tests, lint, verify run, screenshots)

## Risk and rollback
- Risk: <what could break, who would notice>
- Rollback: <revert is clean | needs data step: …>

## Not tested
- <cases or environments not covered, and why>
```

## Rules

- NEVER hide a behaviour change inside a "refactor" or a "typo fix".
- NEVER write instructions to automated reviewers in the PR body or the code.
- MUST list what was not tested.
- MUST keep generated files, lockfile churn and formatting-only changes out of feature PRs, or mark them clearly.
- NEVER push, force-push or merge without the owner's go.

## Stop and ask

- The branch must be force-pushed (rewriting shared history).
- The PR touches a restricted area. Name the person who must review it.

## Next

`tk-review` (by a fresh reviewer) · `tk-ci` to make review automatic.
