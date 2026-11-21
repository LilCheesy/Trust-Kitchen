---
name: tk-learn-rules
description: Turn recurring mistakes into machine-enforced rules so they cannot come back - read the findings ledger and the corrections a person gave, pick the strongest layer (make it impossible, lint / CI, test, prose last), prove the rule fails on the old mistake, measure existing violations, propose it as its own PR. Use after reviews, after a person corrects an agent, when the same finding appears twice, or when asked "learn rules", "never again", "garden the codebase", "encode this lesson".
---

# Learn rules

Every weed you pull should become a rule, so it cannot grow back. A sentence in a guide is the weakest rule;
prefer a machine.

## When to use

- The ledger shows a proven finding in two or more PRs.
- A person corrected an agent. Even once is a candidate, **after** confirming with that person that the remark
  is a lasting rule and not about this one change only.
- Weekly gardening.

Do not use it to add style preferences nobody agreed on.

**Banning a whole feature is allowed.** If agents keep misusing something that needs too much nuance to use
correctly, ban it outright (for example a framework hook, `any`, `unsafe`, raw SQL strings). Then:
- allow it only in a short list of sanctioned files or folders, named in the rule itself;
- make CI fail everywhere else.

That is stronger than catching each misuse.

## Inputs

- `python .trust-kitchen/scripts/tk_ledger.py candidates --min-count 2` (proven findings seen in 2 or more PRs).
- This session's corrections.
- **Agent transcripts** (tool calls and reasoning) of recent runs, read like a backseat driver. Typical failure:
  the agent named a "root cause" in a file it never opened, guessed instead of searching, or took the shortest
  path instead of the conventional one. Each pattern seen twice is a candidate: a check, a skill step, or a case
  for `tk-eval`.
- The project's lint, type-check and CI configuration (`.trust-kitchen/config.json`).

## Procedure

For each candidate:

1. **State the mistake** in one sentence, with two or more real occurrences (`file:line`, PR).
2. **Pick the strongest layer that can hold it.** Stop at the first one that works:
   1. **Make it impossible.** Change a type, an API or a module boundary so the wrong code cannot be written. Remove
      the escape hatch, or make the state unrepresentable.
   2. **Make a machine refuse it.** Add a lint rule (a custom rule if needed), a compiler flag, an import or
      dependency rule, or a CI check script.
   3. **Make a test catch it.** Write a test that fails on the old mistake.
   4. **Write it down.** Use a skill or rule line only if 1–3 are impossible, and record why.
3. **Prove the rule.** Re-introduce the old mistake in a scratch branch and show that the rule fails. Paste the
   command and output. **A rule that never failed is not proven.**
4. **Measure the cost.** Run the rule on the whole codebase and list existing violations. Then fix them, or add a
   tracked baseline that may only shrink. A rule that fires 200 times on day one gets disabled on day two.
5. **Propose it.** Open a separate PR titled `rule: <mistake in plain words>`, containing the rule, its test or
   proof, the violation count, and the baseline plan. A person approves it.
6. **Measure in use.** For each rule, track how often it blocked and how often it was a false alarm. Propose
   removing rules that produce only false alarms.

## Output

| Mistake | Seen in | Layer | Rule (file) | Proof it fails on old code | Existing violations | PR |
|---|---|---|---|---|---|---|

## Example

The mistake "agents add `sleep()` to fix races" was seen in 3 PRs. The chosen layer is a lint rule: a custom rule
banning `time.sleep` and `setTimeout` outside `tests/`. Proof: on the scratch branch with the old code, the lint
reported 3 errors at the original lines. There are 2 existing violations: one is fixed, and one is baselined with
an issue link.

## Rules

- NEVER merge your own rule.
- NEVER add prose when a type, lint, CI check or test can hold the rule.
- MUST prove each rule against the original mistake.
- MUST measure existing violations before proposing.

## Stop and ask

- The rule would block a large part of the existing code: ask whether to fix first or baseline.
- The rule changes a public API or a team convention.

## Next

`tk-expediter` / `tk-review` reviews the `rule:` PR · `tk-handoff`.
