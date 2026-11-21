---
name: tk-investigate
description: Find the root cause of a bug, failure or surprising behaviour without changing anything - reproduce, trace data and control flow, form and test hypotheses, and report the first place where things go wrong with evidence. Use before fixing any bug, or when asked "why does this happen", "investigate", "root cause", "debug this", "don't change code yet".
---

# Investigate (read-only)

A fix applied before the cause is known usually moves the bug somewhere else. Read and run first; edit nothing.

## When to use

- A bug, failing test, crash, wrong number, slowdown or flaky behaviour.
- Before any fix where the cause is not already proven.
- The user says "don't change code yet".

Do not use it when the cause is already proven and written down. Go to `tk-build`.

## Inputs

- The symptom: an error message, failing test, screenshot, log, or the steps the user took.
- The environment where it happens (version, configuration, data).
- Access to run the project locally or in a sandbox.

## Procedure

1. **Restate the symptom** exactly: the input, the expected result, the actual result, and how often it happens.
2. **Reproduce it.** Find the smallest command or test that shows the bug. If you cannot reproduce it, say so and
   collect more facts. Do not guess a fix.
   - Reproduce on the **version the reporter used** and on the **latest default branch**.
   - If it is gone on the default branch, find the commit that fixed it (`git log`, `git bisect`), report it,
     and stop. There is nothing to fix.
   - Use the project's `verify-<app>` skill to drive the app when one exists.
3. **Trace.** Follow the data and the calls from the input to the wrong output. Read the code on that path and the
   library code at the pinned version. Note `file:line` at every step.
   - In a large codebase, fan out **read-only subagents** to locate the code on the path in parallel. Each one
     returns `file:line` with what it saw.
   - Never name a cause in a file nobody opened.
4. **Find the first wrong place.** This is the earliest point where the state is already wrong. A guard placed
   later only hides the problem.
5. **Hypotheses.** List them, then design a check that can **disprove** each one. Run the checks. Keep a short log
   of hypothesis → check → result.
6. **Attack the premise.** If two attempted explanations have failed, question the assumption they share (the
   environment, the version, the data, or what the test really measures).
7. **Check history.** Use `git log -L` or `git blame` on the first wrong place, and find out when and why it
   changed.
8. **Report.** Give the root cause, the evidence, and the smallest fix direction. Do not apply the fix.

## Output

```
Symptom: <input → expected vs actual, frequency>
Reproduction: <command / test>  →  <output excerpt>
First wrong place: <file:line> — <what is wrong there>
Evidence: <hypothesis log: H1 … disproved by …; H2 … confirmed by …>
Why it happened: <commit / change, if found>
Fix direction: <smallest change at the first wrong place>; test that will prove it: <name>
Not explained yet: <anything left over>
```

## Rules

- NEVER edit product code during an investigation. Scratch scripts go in a temporary directory.
- NEVER propose a guard, retry or sleep as the fix unless the state really is legitimate there.
- MUST mark each statement as observed or inferred.
- MUST stop at "cannot reproduce" rather than fix blind.

## Stop and ask

- Reproducing needs production data, secrets or hardware.
- The cause is in another team's system or in a third-party service.

## Next

`tk-build` with the fix direction and its test.
