---
name: tk-review-tests
description: Review whether a change's tests actually prove its behaviour and whether any existing safety net was weakened - deleted / skipped / loosened tests, would-it-fail-without-the-change, behaviour vs implementation, important edges, mocks, determinism, proportion. Use as a tk-review reviewer, or when asked "are these tests good", "test review", "is it really tested", "did they cheat the tests".
---

# Test review

A test that cannot fail proves nothing. A suite that was quietly weakened is worse than no suite.

## When to use

Every review where code or tests changed.

Do not use it to demand tests for trivial changes (renames, docs) that have no behaviour.

## Inputs

- The diff (code and tests).
- The existing tests for the touched area.
- If possible, the ability to run the tests on the base commit and on the head commit.

## Procedure

1. **Safety net intact?** Look for:
   - deleted tests;
   - new `skip`, `only` or `xfail`;
   - removed or loosened assertions (`==` changed to `in`, wider tolerances, `assert True`);
   - snapshots regenerated wholesale;
   - expected values changed to match new output without explanation.
2. **Would it fail without the change?** For each new or changed behaviour, find the covering test and its
   assertion.
   - Best evidence: run it against the base, or with the change reverted, and show red.
   - Otherwise, reason from the assertion.
   - A test whose expected value is computed with the same formula as the code cannot fail on a wrong formula.
3. **Behaviour, not implementation.** Flag tests that re-implement the logic, assert on private calls or call
   order, or only check that a mock was called.
4. **Edges that matter.** Check empty, one, many, boundary (both sides), invalid, error path, duplicate,
   concurrent and time-dependent cases. Name the **important** missing ones. Do not demand every possible case.
   - **Properties, not only examples.** Parsers, serialisation and encoding, state machines, sync, merging and
     concurrency fail on inputs nobody thought of.
   - For these, ask for a **property-based or fuzz test** that states the invariant and runs it on many generated
     inputs. Examples of invariants: decode(encode(x)) == x; a merge is order-independent; no state is reachable
     from "closed".
   - For a critical multi-step or multi-device flow, ask for a **model check**.
   - A missing property test is MINOR, with the invariant and the test named in `fix`. It is MAJOR only under the
     calibration below: when no test at all would fail without the change.
5. **Mocks.** Mock only what the test does not own (network, clock, external services). Mocking the unit under
   test is fake.
6. **Determinism.** Look for real time, unseeded randomness, set or map ordering, network access, or state shared
   between tests.
7. **Proportion.** Is there a big behaviour change with no test change? Are trivial getters tested while the risky
   branch is not?
8. **Smallest proving test.** For each gap, give the input and the expected literal output.

## Output

Findings (`category: tests`), each with the smallest test that would catch the problem.

## Rules

- MUST give literal expected values in suggested tests, not formulas.
- **Severity:**

  | Severity | When |
  |---|---|
  | BLOCKER | a weakened or deleted safety net without an accepted reason, or a test that cannot fail on the claimed fix |
  | MAJOR | a changed behaviour with no test, implementation-testing on a key path, or a flaky construct |
  | MINOR | a missing secondary edge case, or unclear test names |

  - **Calibration (learned from eval case c04).** A changed behaviour counts as *tested* when at least one test
    fails without the change. For a validated range, a test on one side counts.
    - Missing tests for the other side or the exact boundaries are a **MINOR** finding: name the test cases in
      `fix`.
    - It is MAJOR only when no test at all would fail without the change.
  - Never raise severity for a gap you would only call "nice to have".

## Stop and ask

- The PR says a test was removed because the behaviour no longer exists. Ask the owner to confirm the behaviour
  removal.

## Next

Back to `tk-review`.
