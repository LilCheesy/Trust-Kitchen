---
name: tk-spec
description: Write a spec before code for any change larger than a few files or touching security, data, money or hardware - context, current state with evidence, agent contract, scope, behaviour, edge cases, acceptance criteria written before code, limits, file list and test plan. Use when asked "write a spec", "spec this feature", "acceptance criteria", or when tk-plan says the change is too big for four lines.
---

# Spec before code

A spec is the contract the code will be judged against. Writing it **after** the code turns it into a description
of whatever got built.

## When to use

- A change crosses modules, adds a feature, or touches security, data, money, people or hardware.
- More than about 5 files, or work that spans sessions.
- The owner asks for one.

Do not use it for a small, obvious, reversible fix. A four-line plan (`tk-plan`) is enough.

## Inputs

- The goal from the owner, in their words.
- The code as it is today. Read it; do not assume.
- Existing issues, designs and constraints.

## Procedure

1. **Context (2-minute read).** Cover what is happening, the problem, why now, what will be done (plainly), what
   will **not** be done, and how we will know it is done.
2. **Current state with evidence.** Make a table of what you found, each row with its evidence (`file:line`, a
   command and its output, or a measured number) and its evidence level. Do not describe code you did not read.
3. **Agent contract.** State what the agent may do, must not do, and must stop and ask about (see the
   `tk-plan` stop points), plus project-specific bans.
4. **Scope.** List in and out of scope, with a reason for each item that is out.
5. **Behaviour.** Describe the main flow step by step. A diagram helps if it shows the real mechanism.
6. **Edge cases (`EC-nn`).** For each case give when it happens (a real example), what the system does, and the
   state afterwards. Cover empty, maximum, invalid, duplicate, concurrent, partial failure, missing dependency,
   permission denied, and malicious input.
7. **Acceptance criteria (`AC-nn`).** Each criterion is testable and names the test or command that will prove
   it. Write them as `- [ ]`. Tick one only when it is proven in a clean environment (evidence level 3).
8. **Limits.** Declare every number per `tk-limits`, including assumed ones.
9. **Files.** List every file to create or edit, with why (which AC or EC), what it does, and who calls it.
   **A file not on the list may not be touched.**
10. **Test plan.** Say which tests go red first, how they turn green, how you will check in a clean environment,
    and how to break the code to prove the tests bite.
11. **Decisions for the owner.** Write numbered questions with a recommended answer for each.
12. **Status.** Set it to `DRAFT → WAITING_APPROVAL`. Only the owner moves it to `APPROVED`, and later to `DONE`.
13. **Check it by machine** before asking for approval:
    `python .trust-kitchen/scripts/tk_spec_check.py validate SPEC-<AREA>-<nnn>.md`. Fix every error. Do not ask for
    approval with a failing spec.

## Output

A `SPEC-<AREA>-<nnn>.md` file in exactly this frame. `tk_spec_check.py` checks it: the headings are fixed, and
each AC names its test in `code`.

```markdown
# SPEC-<AREA>-<nnn>: <title>

Status: DRAFT | WAITING_APPROVAL | APPROVED | DONE

## Context
## Current state
## Agent contract
## Scope
## Behaviour
## Edge cases
- EC-01 <when (real example)> → <what the system does> → <state after>
## Acceptance criteria
- [ ] AC-01 <testable behaviour> (`test_name` or `command`)
## Limits
## Files
## Test plan
## Decisions
## Log
| When | Who | What | Result |
```

Code and tests that implement a criterion carry a tag next to them: `@spec: SPEC-<AREA>-<nnn>#AC-01` (in a
comment). `tk_spec_check.py anchors` then shows which files prove which criterion. It fails on a tag pointing at
a criterion that does not exist, and on a ticked criterion that no file carries.

## Example

Good: `AC-03 Two concurrent redeems of one coupon apply the discount once (test_redeem_concurrent)`.
Bad: `AC-03 Coupons work correctly`.

## Rules

- MUST write the acceptance criteria before any code.
- MUST give each AC a named test or command.
- NEVER mark an AC done on evidence below level 3.
- NEVER describe the current state without evidence.
- NEVER start coding while the status is `WAITING_APPROVAL`.
- NEVER ask for approval while `tk_spec_check.py validate` reports errors.

## Stop and ask

- The spec needs a threshold, limit or policy value: the owner decides.
- Scope keeps growing while you write: split into several specs.

## Next

Owner approval, then `tk-build` (step by step) or `tk-head-chef` to slice the work.
