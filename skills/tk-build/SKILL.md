---
name: tk-build
description: Implement an approved change in small verified steps - red test first, smallest change to green, clean up, run the project's checks, self-scan the diff - staying strictly inside the approved files. Use when an approved plan or spec step is ready, or when asked "implement", "build it", "make the change", "fix it" after the cause is known.
---

# Build: red, green, clean

Each step ends in a check. The diff stays small enough that someone else can review it properly.

## When to use

- An approved four-line plan or spec step exists.
- For a bug: the root cause is known (`tk-investigate`).

Do not use it without approval, or while the cause of a bug is still unknown.

## Inputs

- The approved plan or spec, including its file list and acceptance checks.
- `.trust-kitchen/config.json` for the build, lint, type-check and test commands.

## Procedure

For each step of the plan:

1. **Red.** Write the test that states the expected behaviour (or the bug repro). Run it and paste the failure.
   It must fail **for the reason you expect**. A test that fails because of an import error does not count.
   When the work has a spec, tag the test and the code that implements the criterion with
   `@spec: SPEC-<AREA>-<nnn>#AC-nn` in a comment.
2. **Green.** Make the smallest change that passes. Prefer deleting over adding. Fix at the first wrong place,
   not where the symptom appears.
3. **Clean.**
   - Remove dead code, debug output and impossible-state guards.
   - Do not leave comments that explain hacks.
   - Do not rename or reformat outside the change.
4. **Self-scan.** Run `python .trust-kitchen/scripts/tk_scan.py --base <default_branch>` and fix every hit your
   step introduced.
5. **Checks.** Run lint, type check, and the tests for the area, then the full suite if it is affordable. Paste
   the results. With a spec, also run
   `python .trust-kitchen/scripts/tk_spec_check.py anchors <spec> --root .`. It must report no errors before you
   tick an AC.
6. **Behaviour proof.** If the step changes behaviour that a user can see, run it for real (`tk-review-verify`).
7. **Commit** the step on its own, with a message that says what changed and why.
8. **Update state.** Mark the step as proven, with its evidence, in `.trust-kitchen/state.md`.

## Output

Per step: the red output, the green output, the check results, and the commit id. At the end, a six-part report
(`tk-report`).

## Rules

- MUST stay inside the approved file list.
- MUST see red before green.
- NEVER loosen, skip, delete or rewrite an existing test to pass. If an existing test is wrong, stop and ask.
- NEVER mix refactoring and behaviour change in one commit.
- NEVER add suppressions (`noqa`, `ts-ignore`, `eslint-disable`) without a linked reason the owner accepted.
- NEVER review or merge your own change.

## Stop and ask

- You need a file outside the plan.
- Green requires changing an acceptance criterion.
- The step grows beyond about 300 changed lines. Split it.
- Anything on the `tk-plan` stop list.

## Next

`tk-pr` to open the PR, then `tk-review` by a fresh reviewer.
