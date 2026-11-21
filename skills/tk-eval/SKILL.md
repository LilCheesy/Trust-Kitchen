---
name: tk-eval
description: Measure any Trust Kitchen skill (and a project's own verify skill) on cases whose expectations were written before the run, like unit tests for skills - catch rate and false alarms for reviewers, rubric pass rate for every other skill, blind copies so the agent cannot tell it is being measured, a second judge from another model, and a tune set you climb to 10/10 with a holdout set that tells the truth. Use every time a skill changes, before turning on auto-merge, or when asked "how good is this skill", "eval the skills", "did this change make it worse".
argument-hint: "[nothing | a cases folder | --split holdout]"
---

# Evaluate the skills

A skill is a process you measure, like code with unit tests: every time a skill changes, its cases run. Without
numbers, "the skill got better" is a feeling.

## When to use

- After **any** change to a skill, a reviewer, the scanner or a project's `verify-<app>` skill.
- Before turning on auto-merge for a repository.
- Periodically, with new cases from escaped bugs and from failures seen in agent transcripts.

Do not use it with cases written after seeing the output. Expectations come first.

## Inputs

- Cases in `.trust-kitchen/evals/cases/<id>/case.json`, with `id`, `title`, `layer`, `clean`, `split` and
  `expect`. The installer puts example cases there. Add your project's own cases next to them; replace the examples
  once you have enough of your own.
  - `layer` is `deterministic`, `review` or `skill`.
  - `split` is `tune` (the default) or `holdout`.
- The input next to it:
  - `diff.patch` for `deterministic` and `review` cases;
  - `task.md` for `skill` cases.
- The expectations:
  - Reviewer cases: `expect` is a list of `{rule | category, file}`.
  - Skill cases: `skill` names the skill under test, and `expect` is a rubric, a list of
    `{id, check}` where each check can be answered yes or no.
- Targets: catch rate, false-alarm rate, and rubric pass rate. The defaults (0.8 and 0.1) are assumed; the team
  sets its own.

## Procedure

1. **Score the deterministic layer** (live): `python .trust-kitchen/evals/run_eval.py`. Below, `run_eval.py` means
   that file.
2. **Make blind copies.** An agent that can tell it is being measured behaves differently.
   - Run `python run_eval.py blind <out> --seed <new seed>`.
   - Each case lands in `<out>/work/item-<hash>/`, holding only `change.patch` or `task.md` and `request.md`.
   - The key goes to `<out>/key.json`. **Give the agent `<out>/work/<item>` only, never the key, the cases folder
     or `case.json`.**
   - Use a new seed for every run.
3. **Run the skill under test.** For each item:
   - start a fresh agent;
   - run the skill (`tk-review` for reviewer cases, the case's `skill` otherwise) on that folder alone;
   - save the result as `results/<item>.json`:
     - reviewers: `{"findings": [...]}`;
     - other skills: the agent's transcript and output, then the judge's `{"rubric": {"<id>": true|false}}`.
4. **Judge twice, with two models.**
   - A judge scores each rubric item from the transcript: did the agent actually do it?
   - Run a **second judge on a different model** into a second folder.
   - Cases where the two disagree are **unstable**: fix the case or the rubric wording, not the score.
5. **Score:**
   `python run_eval.py --results <dir> --second <dir2> --key <out>/key.json --split tune`.
   - An empty selection (no cases in that split) is a FAIL, never a pass.
   - A reviewer hit counts only if it is proven (confidence ≥ 3) and matches the expected rule or category and
     file.
   - A clean case is a false alarm when it receives a proven BLOCKER or MAJOR.
   - Missing results are **NOT RUN**, never 0.
6. **Climb the tune set to 10/10.** Change the skill, rerun the tune cases, repeat until every tune case passes.
   This is the goal, not a warning sign.
7. **Then run the holdout set once**, with `--split holdout`.
   - It is never looked at or tuned on. Its number is the honest one.
   - If holdout is much worse than tune, the skill learned the cases rather than the job. Write new cases, do not
     tune on holdout.
8. **Compare before and after** a skill change, on both sets, and report both.
9. **Grow the set from reality.**
   - Every escaped bug becomes a new case, with its expectation written first and private code removed.
   - So does every failure pattern seen in agent transcripts (`tk-learn-rules`).
   - Put about one case in three into holdout.

## Output

```
split: tune | holdout
deterministic: <caught>/<expected> (<rate>)
review: <caught>/<expected> (<rate>) · not run: <n>
skills: <skill> <passed>/<expected> (<rate>) · failed: <case: item> ...
clean: <false alarms>/<judged> (<rate>) · alarms: <case ids>
stability: <agree>/<compared> · unstable: <case ids>
result: PASS | FAIL (<reasons>) · targets: <values, assumed|agreed>
before → after: <rates on tune> · <rates on holdout>
```

## Rules

- NEVER edit a case's expectation to match a result. A wrong expectation is fixed in its own commit, with a
  reason.
- NEVER tune on the holdout set, or show it to the agent being improved.
- NEVER give the agent the key, `case.json`, or a path that names the case.
- NEVER change a skill without reporting the before and after numbers.
- MUST report NOT RUN rather than treating missing results as zero.
- MUST treat a perfect **holdout** score as a reason to check how the cases were written (were they written for
  this skill?). A perfect tune score is the target.

## Stop and ask

- The targets have not been agreed for this repository. The owner sets them.
- A skill change improves catch rate but worsens false alarms. The owner decides the trade-off.
- The two judges keep disagreeing on the same case after a rewording.

## Next

`tk-merge-gate` (auto-merge readiness) · `tk-learn-rules` (repeated misses become scanner rules).
