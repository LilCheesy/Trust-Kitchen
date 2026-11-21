---
name: tk-principles
description: The Trust Kitchen working rules that every other tk-* skill assumes - the trust stack, evidence before claims, the author never grades their own work, every correction becomes a rule, small reversible steps, honest numbers, trust before parallelism. Read first in any session that uses Trust Kitchen, or when asked "how should agents work here", "trust kitchen principles", "why so strict".
---

# Trust Kitchen principles

Agents produce code faster than anyone can read it. Output is no longer scarce; **trust** is. Trust Kitchen exists
so that more output never means lower quality.

## When to use

- At the start of a session in a project that uses Trust Kitchen. Read it once.
- When a decision is unclear and you need the underlying rule.
- When someone asks why a step (red test, fresh reviewer, evidence) is required.

Do not use it as a substitute for the specific skill. The principles explain *why*; the skills say *how*.

## Inputs

None. This is the shared foundation.

## Procedure

Apply these seven principles to every task.

1. **Put each rule in the strongest layer that can hold it.** From strongest and cheapest to weakest and most
   expensive:

   | # | Layer | Examples | Why |
   |---|---|---|---|
   | 1 | Code shape | types, module boundaries, APIs that make the wrong call impossible | the mistake cannot be written |
   | 2 | Static checks | compiler, linter, tests, CI | a machine says no every time |
   | 3 | Runtime proof | run it, capture output, screenshots, traces | behaviour is observed, not argued |
   | 4 | Written guidance | skills, rules, AGENTS.md | agents can skip it |
   | 5 | A person reading the diff | review | the scarcest resource |

   Before writing a sentence of guidance, ask whether a type, a lint rule or a test could say it instead.
2. **No claim without evidence.** Every claim carries its evidence level (0–5, see `tk-evidence`). "It compiles"
   proves nothing about behaviour. If a check could not run, the answer is *inconclusive*.
3. **The author never grades their own work.** Review runs in a fresh context that sees the diff and the stated
   intent, not the author's reasoning. A machine may score; only the owner accepts.
4. **Every correction becomes a rule.** A mistake found twice is a missing rule. Encode it in the strongest layer
   and prove it catches the old mistake (`tk-learn-rules`).
5. **Small, reversible, stoppable.**
   - Make the smallest change that meets the goal.
   - Say what you will do before doing it (`tk-plan`), and stay inside what was approved.
   - Irreversible actions always stop for a person.
6. **Numbers tell the truth about themselves.**
   - Label each number MEASURED, COMMANDED or ASSUMED.
   - Missing data is shown as NO DATA, never 0.
   - Anything relying on an assumed limit is never called "safe" (`tk-limits`).
7. **Trust first, then parallel.** Add more agents only when you can verify what they produce. Parallel reviewers
   work because each one is narrow, fresh, and must prove its findings.

## Output

None by itself. Other skills cite these principles by number when a decision depends on them, for example
"principle 3: handed review to a fresh agent".

## Rules

- MUST treat these principles as defaults that a project can make stricter, but not weaker, without the owner's
  written decision.
- NEVER cite a principle to justify skipping evidence.

## Stop and ask

- Two principles conflict in a concrete case (for example, speed versus a stop point). Ask the owner, and do not
  pick silently.

## Next

`tk` (hub) · `tk-plan` (before any change).
