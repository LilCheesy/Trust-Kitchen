---
name: tk-review-intent
description: Review a change as the product owner would - does it do what it claims, what the user and the business need, and nothing else - claim vs diff, hidden behaviour changes, acceptance criteria, user-visible impact, business edge cases, rollout, rollback and cost. Use as a tk-review reviewer, or when asked "does this PR do what it says", "scope creep", "business review", "is this the right change".
---

# Intent and business review

Correct code that solves the wrong problem is still waste. A small "cleanup" that changes prices is a business
incident.

## When to use

Every review. This is the reviewer that keeps the developer view and the business view together.

Do not use it to judge code style or design. Other reviewers own those.

## Inputs

- The diff and the PR description.
- The linked issue, spec or acceptance criteria.
- Any product docs that describe the behaviour.

## Procedure

1. **Claim vs diff.** Make two lists: what the description says changes, and what the diff actually changes.
   - **Missing**: claimed but not in the diff.
   - **Hidden**: in the diff but not mentioned. Look closely at config values, defaults, constants, rounding,
     timeouts, feature flags, permissions, messages, and anything in "typo" or "cleanup" PRs.
2. **Requirement fit.** Map each acceptance criterion to the code and the test that meet it. A criterion met only
   by a comment or a TODO is unmet.
3. **User-visible behaviour.** For each change, say who notices it and what they see before and after: changed
   defaults, prices, units, rounding, limits, error messages, emails, removed options, permission changes.
4. **Business edges.** Check zero, negative, empty, maximum, duplicate, concurrent, other currency, locale or time
   zone, partial failure, refund or cancel paths. Decide whether **the rule itself** is right, not only whether the
   code is consistent.
5. **Rollout and rollback.**
   - Can it ship behind a flag?
   - Does a data or format change block a rollback?
   - Who must be told: support, docs, other teams, customers?
6. **Cost and value.** Look for new paid calls, heavy jobs, more storage or more alerts. Is the cost in proportion
   to the claimed value?

## Output

Findings in the Trust Kitchen format (`category: intent`), plus a summary:

```
Really does: <1 line>
Affects: <who>
Undo: <how>
```

## Rules

- MUST report every hidden behaviour change, even if it looks harmless.
- MUST tie each finding to a user or business consequence, not to taste.
- **Severity:**

  | Severity | When |
  |---|---|
  | BLOCKER | the change does the opposite of its intent, breaks a documented promise to users, or is risky with no possible rollback |
  | MAJOR | unmet criterion, hidden behaviour change, or an unhandled business edge |
  | MINOR | an unclear user-facing message, or a missing docs or changelog entry |

## Stop and ask

- The business rule is ambiguous (for example "round prices how?"). Ask the owner; do not decide.

## Next

Back to `tk-review` (merge step).
