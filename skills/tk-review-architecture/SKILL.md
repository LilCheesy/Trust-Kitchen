---
name: tk-review-architecture
description: Review the shape of a change - data model, impossible states, one owner per state, boundaries, public API, needless layers, duplication, migration discipline, domain model, idempotency - and whether it makes the next mistake easier or impossible. Use as a tk-review reviewer when a change adds modules, types, public APIs or crosses boundaries, or when asked "architecture review", "is this the right abstraction", "design review".
---

# Architecture review

Agents copy whatever shape already exists. A bad shape merged today gets copied ten times next month.

## When to use

- New modules, public APIs, types or data models.
- Changes that cross a module or layer boundary.
- Refactors.

Do not use it for small local edits inside one function that keep its contract.

## Inputs

- The diff.
- Surrounding code: the callers, the types, the module layout, and the existing patterns for the same problem.

## Procedure

1. **Data first.** Name the core data shape the change adds or changes. Ask whether impossible states are
   impossible:
   - contradictory boolean pairs;
   - optional fields that are "always set in practice";
   - ids, money and units passed as bare strings or numbers;
   - stringly-typed states.
2. **One owner per state.** Each piece of state has exactly one writer. Flag mirrored flags, duplicated caches,
   and anything "kept in sync by convention".
3. **Boundaries.**
   - Parse and validate at the edges: input, network, files, database. Inside, trust the types.
   - Flag re-validation deep inside the code.
   - Flag business logic in handlers or views.
   - Flag imports across layers that should not know each other.
4. **Public API.**
   - Make the right call the easiest call.
   - Flag APIs that need a comment to be used safely.
   - Flag boolean flags that switch behaviour.
   - Flag option bags whose options interact.
5. **Smallest shape.** Prefer deletion. Flag:
   - one-caller wrappers;
   - layers that only forward calls;
   - abstractions with a single use;
   - three or more copies of the same code;
   - a function doing two jobs behind a flag.
6. **Migration discipline.** When an API is replaced, all callers must move and the old one is deleted in the same
   wave. Two ways to do the same thing invite agents to use the wrong one.
7. **Domain model.** A third special case in a third place means a concept is missing. Name the concept.
8. **Idempotency.** Can jobs, retries and webhooks run twice safely?

## Output

Findings (`category: architecture`). Each finding proposes the shape that removes the problem (types or
signatures) and says whether it can be **encoded** (import rule, type, lint).

## Rules

- MUST propose a concrete alternative shape for each MAJOR or higher.
- NEVER ask for abstraction "for the future". Ask only when the present code needs it.
- **Severity:**

  | Severity | When |
  |---|---|
  | BLOCKER | a data-corruption risk, two writers on a concurrent path, or a security-relevant mistake made the easy path |
  | MAJOR | a new boundary violation, a duplicated source of truth, or a misleading public API |
  | MINOR | wrappers or abstraction that add reading load |

## Stop and ask

- The change implies a wider redesign than the PR. Recommend a separate design discussion; do not block a small,
  correct change for it.

## Next

Back to `tk-review`.
