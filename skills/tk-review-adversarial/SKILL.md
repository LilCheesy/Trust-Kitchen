---
name: tk-review-adversarial
description: Attack a change with several independent adversaries (hostile inputs, state and time, misuse) trying to break it, keep only findings a run reproduces, and report Intent / Findings / Dropped without fixing anything. Use for risky, large or contested changes, or when asked "try to break this", "adversarial review", "stress test this PR", "red team this code".
---

# Adversarial review

The adversaries try to break the change. A finding survives only when a run proves it.

## When to use

- Risky changes: money, auth, concurrency, parsing, data.
- Contested designs, or diffs over 200 lines.

Do not use it on systems you do not own. All attacks run in a local sandbox against the change's own code.

## Inputs

- The diff and the restated intent (from `tk-review`).
- A way to run code locally: tests, scripts, a sandbox.

## Procedure

1. **Frame.** Choose three adversaries, using a different model for each if you can:
   - **Inputs**: hostile, empty, huge or malformed inputs; unicode; boundaries.
   - **State and time**: concurrency, retries, ordering, partial failure, restarts, clock changes.
   - **Misuse**: callers using the API unexpectedly; permissions; configuration.
2. **Fan out in parallel.** Each adversary gets the diff, the intent and this brief:
   - Make the change violate its intent or harm users.
   - For each attempt, write a repro (test, script or command) in a scratch directory.
   - Report only failures you reproduced.
   - Leave out style and "might be a problem someday".
   - "No findings" is valid.
3. **Verify.** Re-run each repro yourself. Keep a finding only when the output shows the failure **and** the
   failure breaks the intent. Merge findings that share a root cause.
4. **Report.**

## Output

```
Intent: <restated>
Findings: <command · output excerpt · how it breaks intent · which adversary>   (or "no verified findings")
Dropped: <per adversary: count + reason (not reproducible / out of scope / style)>
```

Surviving findings get confidence 4–5, in the Trust Kitchen format.

## Rules

- NEVER apply fixes, and never push repro code into the change.
- NEVER run repros against production or third-party systems.
- MUST re-run every reported repro yourself before keeping it.

## Stop and ask

- A repro needs real credentials or external services.

## Next

Back to `tk-review`.
