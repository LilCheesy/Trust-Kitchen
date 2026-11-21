---
name: tk-plan
description: Say what you will do before touching anything - four lines (will do, files, how to check, needs you) - then wait for explicit approval, and stop at the eight stop points. Use at the start of every task that changes files or runs actions, or when asked "plan first", "what will you change", "4-line plan". Keeps the agent inside an approved scope.
---

# Plan in four lines, then wait

A plan costs a minute to write and saves an hour of undoing.

## When to use

- Before every edit, write action or external call, even small ones.
- When scope changes mid-task (write a new plan).

Do not use it for read-only investigation; read freely. If the change is large, use `tk-spec` instead of four
lines.

## Inputs

- The request.
- What you have read so far: the relevant files and the current behaviour.

## Procedure

1. **Read before planning.** Open the files you expect to change. A plan about code you have not read is a guess.
2. **Write the four lines:**

   ```
   Will do:       <one sentence: the change and its user-visible effect>
   Files:         <each file created or edited, and why each one is needed>
   How to check:  <the exact test / command / observation that will prove it worked>
   Needs you:     <decisions you will NOT take alone> (or "nothing")
   ```

3. **Size check.** If any of these is true, switch to `tk-spec`:
   - more than about 5 files;
   - crosses module boundaries;
   - touches security, data, money, people or hardware;
   - spans sessions.
4. **Wait for an explicit go.** Silence, "hmm" or a new question is not approval. Approval for one plan does not
   carry over to the next.
5. **Execute inside the plan.** Track every file you touch against the list.
6. **Re-plan on change.** Needing anything not in the plan means stop, write a new plan, and wait again.

## Output

The four-line block, and after approval, work that stays inside it.

## Example

Good:

```
Will do:       Reject cart quantities outside 1–99 with HTTP 422.
Files:         app/api/cart.py (validation), tests/test_cart_api.py (edge tests 0, 1, 99, 100).
How to check:  pytest tests/test_cart_api.py -q → 4 new tests red before, green after.
Needs you:     Is 99 the right maximum? (taken from the ticket, not from any config)
```

Bad: `Will do: improve cart validation. Files: some API files. How to check: test it.`

## Rules

- MUST name every file. "Some files" is not a plan.
- MUST give a runnable check. "Review it" is not a check.
- NEVER start before an explicit go.
- NEVER treat approval as permanent.

## Stop and ask

Always stop and ask when:
1. A decision belongs to the owner (thresholds, values, standards, naming that others depend on).
2. You need a file or action outside the approved plan.
3. A test fails and the only way to green is to change the criterion or loosen the test.
4. You are about to push, merge, delete, force, or do anything hard to undo.
5. The work touches safety: people, devices or hardware.
6. The work touches sensitive data: customer data, licensed data or secrets.
7. A result looks strange: 100 %, much too fast or slow, or very different from last time. (Exception: a
   `tk-eval` **tune** set climbed to 10/10 is the goal; a perfect **holdout** score still stops here.)
8. You find that something you reported earlier was wrong. Correct it at once.

## Next

`tk-build` (after approval) · `tk-spec` (if too large).
