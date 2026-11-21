---
name: tk-merge-gate
description: Decide MERGE, CHANGES_REQUESTED or NEEDS_HUMAN from review facts with a fixed, testable policy - red checks or proven BLOCKER/MAJOR request changes; restricted areas, unverified behaviour, oversized diffs, reviewer conflicts or exhausted budget need a person; unproven findings never block; auto-merge only on opt-in and never for restricted areas. Use as the last step of tk-review, when configuring auto-merge, or when asked "can this be merged", "merge policy", "should the bot merge it".
---

# Merge gate

The decision to merge is a rule anyone can read and test, not a feeling.

## When to use

- The last step of every review.
- When setting or changing a repository's merge policy, or turning auto-merge on or off.

Do not use it to merge. The gate only decides; a person or CI acts on the decision.

## Inputs

`facts.json` with these keys:

| Key | Meaning |
|---|---|
| `deterministic` | `passed` / `failed` / `inconclusive` (only `passed` can MERGE; anything else, or missing, needs a person) |
| `verify` | `passed` / `failed` / `inconclusive` / `not_applicable` |
| `changed_lines` | int |
| `areas` | from `tk_scan` |
| `findings` | merged findings |
| `conflicts` | list |
| `budget_exhausted` | bool |
| `docs_only` | bool |

Optionally `.trust-kitchen/policy.json`: `auto_merge`, `max_lines`, `min_confidence_to_block`.

## Procedure

1. Run:

   ```
   python .trust-kitchen/scripts/merge_gate.py facts.json --policy .trust-kitchen/policy.json
   ```

2. The built-in policy:

   | Verdict | When |
   |---|---|
   | **CHANGES_REQUESTED** | deterministic checks failed, **or** any BLOCKER / MAJOR with confidence ≥ 3 |
   | **NEEDS_HUMAN** | deterministic checks not `passed` (inconclusive, skipped, missing), **or** a restricted area (auth, security, migration, infra, ci, review-config, dependencies, and the project's `restricted_paths`), **or** behaviour not verified by a run (docs-only excepted), **or** a diff over the team's `max_lines` cap (no cap by default), **or** reviewer conflicts, **or** an exhausted budget |
   | **MERGE** | none of the above |

   - CHANGES_REQUESTED wins over NEEDS_HUMAN.
   - Findings with confidence < 3 are listed as *unproven* and never block.
   - `auto_merge` is true only for MERGE **and** with an opt-in policy **and** no restricted area.
   - Size is advice, not a gate: above 400 changed lines the verdict carries a `notes` line asking for atomic PRs.
     A team that wants a hard cap sets `max_lines` in its policy.

3. Report the verdict, the reasons, the blocking findings and the unproven findings exactly as returned. Exit codes:
   0 MERGE, 2 NEEDS_HUMAN, 3 CHANGES_REQUESTED.

## Output

The gate's JSON (`verdict`, `auto_merge`, `reasons`, `notes`, `blocking`, `unproven`), and one line for the review
report.

## Rules

- NEVER auto-merge a restricted area, whatever the policy file says. This is hard-coded.
- NEVER let unproven findings block.
- NEVER change the gate's code without updating its tests in the Trust Kitchen repository, and rerunning
  `tk_selfcheck.py`. Changing the gate changes what ships without a person.
- Before turning on auto-merge for a repository, all of these MUST be true:
  1. the deterministic layer runs in CI and blocks (`tk-ci`);
  2. `tk-eval` meets the repository's catch-rate and false-alarm targets;
  3. merges are reversible (clean revert, deploys roll back);
  4. **the foundation holds.** Automation on a loose codebase only produces more slop, faster. So:
     - the project's lint, type check and import-boundary checks block in CI;
     - the conventions agents must follow are encoded as checks, not only written down;
     - `tk-review-code` on the core modules is not AT RISK.

  After turning it on:
  - a person reads a sample of auto-merged PRs every week;
  - the revert rate is tracked, and auto-merge switches off automatically when it rises above the agreed threshold.

## Stop and ask

- Someone asks to auto-merge a restricted area. Refuse, and explain.
- A person wants to override a verdict. Accept it, with a written reason recorded in the PR.

## Next

`tk-sous-chef` (on CHANGES_REQUESTED) · a named person (on NEEDS_HUMAN) · merge (on MERGE).
