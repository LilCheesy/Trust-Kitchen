---
name: tk-review-blast-radius
description: Find what a change can break outside its own diff and prove the one fact its safety depends on - behaviour change, safety fact, places grep does not reach (dynamic calls, pinned library behaviour, timing, non-code consumers), honest risk list, cheapest proof. Use as a tk-review reviewer for shared code, public APIs, data formats or config, or when asked "what could this break", "blast radius", "is this safe for callers", "I don't trust this small diff".
---

# Blast radius

A convincing explanation reads the same whether it is true or not. Listing the callers is not the job; proving
they still work is.

## When to use

- Changes to shared helpers, public APIs, defaults, config, data formats or libraries.
- Small diffs in central places ("just one line").

Do not use it for code that nothing else calls (a new leaf module). Say so and skip.

## Inputs

- The diff.
- The repository, so you can search callers and consumers.
- The pinned versions of dependencies, so you can read library code.

## Procedure

1. **Behaviour change.** State what now happens differently: inputs accepted, outputs, errors, timing, ordering,
   side effects, performance.
2. **Safety fact.** Write the one or two facts the change is safe *because of*. Examples: "every caller passes a
   sorted list"; "no stored record has null here"; "this runs after init".
3. **Look where grep stops.**
   - Dynamic dispatch, reflection, string-built names, dependency injection, plugins.
   - Library behaviour at the **pinned** version: read the source, not your memory.
   - When code runs: startup, shutdown, async ordering, retries, caches.
   - Consumers that are not code: stored JSON, DB columns, message formats, public URLs, CLI flags, environment
     variables, feature flags, dashboards, other services.
4. **Prove the safety fact.** Run a script or test against the real code with the risky input. Confidence 2
   ("pointed at the line") is not enough to clear a risk on a shared path.
5. **List risks honestly.** For each risk give how it breaks and where (`file:line`), its likelihood, its cost, and
   the cheapest check. List cleared risks separately, with the evidence that cleared them.

## Output

```
Behaviour change: <1–2 lines>
Safety fact: <fact> — proven at confidence <n> by <command/output> | UNPROVEN
Risks: <file:line · how · likelihood · cost · check>
Cleared: <risk · evidence>
Before merging: <cheapest test/script proving the safety fact>
```

Also give findings (`category: blast-radius`) for risks that are not cleared.

## Rules

- MUST name the safety fact explicitly.
- MUST raise a MAJOR when the safety fact is unproven on a shared or public path, even if the code looks fine.
- NEVER clear a risk on reasoning alone when a cheap run could prove it.

## Stop and ask

- The consumers are in other repositories or teams. Ask who owns them before declaring them unaffected.

## Next

Back to `tk-review`.
