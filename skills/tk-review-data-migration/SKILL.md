---
name: tk-review-data-migration
description: Review changes to stored data - schema migrations, serialized formats, config shapes, message and API contracts - for existing data, locking and size, idempotency, rollback, compatibility during deploy overlap, and personal data. Use as a tk-review reviewer when a migration, model, schema, file format or contract changes, or when asked "is this migration safe", "can we roll back".
---

# Data and migration review

Code rolls back in a minute. Data often cannot.

## When to use

- Migrations, model or schema changes, serialised formats (JSON, events, files), config shapes, API contracts.

Do not use it for in-memory-only refactors with no stored or transmitted format change.

## Inputs

- The diff (the migration and the code that reads and writes the data).
- Knowledge of existing data: ask for row counts and old versions still in use.

## Procedure

1. **Existing data.** What already exists in the old shape (rows, files, queued messages, caches)? Will the new
   code read all of it correctly, including nulls, old enum values and old versions?
2. **Locking and size.** Will it lock a big table, rewrite every row, or outlast a deploy window? Prefer the
   expand-and-contract pattern:
   1. add a nullable field;
   2. dual-write;
   3. backfill in batches;
   4. switch reads;
   5. remove the old field later.
3. **Idempotent and resumable.** Can it run twice? Can it be stopped and restarted?
4. **Rollback.** Is there a down path? A one-way change (data dropped or transformed with loss) must be stated in
   the PR and accepted by a person. Old code must keep working against the new schema during the deploy overlap.
5. **Contracts.** Are old clients, stored documents and other services still compatible? Is the version bumped?
6. **Proof on a copy.** Best evidence: run the migration on a copy or a fixture with realistic edge rows, then read
   the values back (`tk-review-verify`).
7. **Personal data.** New fields or exports holding personal data need a stated reason, access control and
   retention.

## Output

Findings (`category: data`), plus a rollback statement: `clean revert | needs <steps> | one-way (accepted by …)`.

## Rules

- NEVER accept a one-way data change without explicit acceptance from a person.
- MUST check that old code works with the new schema during the deploy overlap.
- **Severity:**

  | Severity | When |
  |---|---|
  | BLOCKER | data loss or corruption, or an irreversible change without acceptance |
  | MAJOR | a long locking migration, a non-idempotent backfill, or a contract break |
  | MINOR | a missing down migration for a reversible change |

## Stop and ask

- Real data volumes or old client versions are unknown. Ask before judging locking or compatibility.

## Next

Back to `tk-review`. Migrations are a restricted area: the merge gate always routes them to a person.
