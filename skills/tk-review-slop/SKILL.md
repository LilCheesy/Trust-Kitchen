---
name: tk-review-slop
description: Find AI slop and quick-fix debt in a change - code that hides a problem instead of solving it or adds weight without value - symptom fixes, swallowed errors, impossible-state guards, excuse comments, suppressions, copy-paste, needless abstraction, dead weight, churn, fake completeness. Use as a tk-review reviewer, or when asked "is this slop", "clean this PR", "AI garbage code", "workarounds".
---

# Slop review

Slop makes the immediate error disappear while making the codebase worse. It spreads because agents imitate what
they see.

## When to use

Every review where code changed.

Do not use it for behaviour correctness or business rules. Other reviewers own those.

## Inputs

- The diff.
- The deterministic scanner's hits (as leads, not verdicts).
- Surrounding code, to judge whether a guard or catch is legitimate.

## Procedure

1. **Start from the scanner leads.** For each hit, either confirm it with the traced reason or dismiss it with the
   reason. Dismissals are part of the output.
2. **Look for these patterns:**

   | Pattern | Looks like | Harm |
   |---|---|---|
   | Symptom fix | `sleep`, `setTimeout`, retries, polling, bigger timeouts added to make a bug or test go away | hides a race or ordering bug |
   | Swallowed error | empty catch, `except: pass`, `catch → return null`, log-and-continue on errors that matter | silent wrong data |
   | Impossible-state guard | null or type checks for values the types guarantee; "just in case" branches | noise implying a contract nobody has |
   | Excuse comment | HACK / workaround / temporary / for now / TODO, long comments explaining strange code | the next agent copies the hack |
   | Suppression | `noqa`, `ts-ignore`, `eslint-disable`, `type: ignore`, `nolint` | the checker was usually right |
   | Copy-paste | near-identical blocks | fixes land in one copy only |
   | Needless abstraction | one-implementation interface, factory for one class, unused config | reading cost, no benefit |
   | Dead weight | unused params or exports, unreachable code, commented-out code, debug leftovers | confuses readers and agents |
   | Churn | renames, reformatting or reordering unrelated to the intent | hides the real change |
   | Fake completeness | stubs returning constants, reachable `NotImplemented`, mock data in product code | looks done, isn't |

3. **Trace legitimacy.** A guard or catch is legitimate only if the state it handles can really occur. Show the
   path that produces that state, or report the guard as slop.
4. **Comments.** Two kinds are judged differently.
   - **The header block** of a function, class or module is documentation for the owner, and is kept. It covers
     what it does, why, when it runs, what it affects, cautions and changes. Check only that it matches the code:
     a stale header is a MAJOR finding, because a wrong comment is worse than none.
   - **Comments inside the body** must earn their place. Keep one only if it says what code cannot: a reason
     grounded in the problem, a reference, or an external constraint.
   - **Delete, or encode,** body comments that:
     - **justify a shortcut** ("workaround", "for now", "don't touch");
     - **use a person or a review as the reason**: "X said never…", "as the reviewer asked", "per code review".
       A one-off remark turns into a permanent rule that nobody can check, and agents copy it everywhere. If the
       remark was meant as a lasting rule, confirm that with the person, then encode the rule itself.
   - If a comment states a constraint ("do not remove", "must stay in this order"), propose encoding it as a type,
     test, lint rule or assertion, and then deleting the comment.
5. **Root-cause fix.** For each finding, give the fix at the cause, not a nicer workaround.

## Output

Findings (`category: slop`) with fix and encode. Example encodes: a lint rule banning `sleep` outside tests, a
rule against suppressions without an issue link, a rule against empty catch blocks. Also list the dismissed
scanner hits, with reasons.

## Rules

- NEVER flag a pattern without checking whether it is legitimate here.
- MUST propose an encode rule for every MAJOR.
- **Severity:**

  | Severity | When |
  |---|---|
  | MAJOR | a symptom fix, swallowed error or fake completeness on a real path; a suppression hiding a real issue |
  | MAJOR | a header block that contradicts the code |
  | MINOR | excuse comments, comments citing a person or review as the reason, needless abstraction, dead code, debug leftovers |
  | NIT | small churn |

## Stop and ask

- A workaround is there because of a third-party bug. Ask whether to keep it, with a tracked issue, instead of
  forcing a "root-cause" fix that is impossible.

## Next

Back to `tk-review` · recurring patterns go to `tk-learn-rules`.
