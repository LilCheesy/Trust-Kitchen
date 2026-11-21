---
name: tk-review-performance
description: Review a change for performance and cost regressions on hot paths (N+1 queries, unbounded work, quadratic loops, blocking calls, memory growth, bundle size, paid calls per request) and vet any performance number it claims with seven questions. Use as a tk-review reviewer when queries, large loops, rendering, startup, caching or concurrency change, or when asked "is this slow", "perf review", "check this benchmark".
---

# Performance review

Only where performance can matter, and every number must explain what limits it.

## When to use

- Database or IO access, loops over data that grows, rendering, startup paths, caching, concurrency.
- The PR claims "faster", "lighter" or "cheaper".

Do not use it for cold paths with bounded, small inputs. Say "not on a hot path" and skip.

## Inputs

- The diff.
- Data sizes: ask, or infer from fixtures and docs.
- Any benchmark output the PR provides.

## Procedure

1. **Locate the hot path.** Where does this code run, and how often? With what input size today, and what
   growth?
2. **Look for:**
   - **Database / IO**: queries in loops (N+1); missing index for a new filter; unbounded `SELECT`; whole files or
     tables loaded into memory; chatty network calls; missing pagination.
   - **Algorithms**: nested loops over growing data; repeated sort or parse; string building in loops; regex
     backtracking on user input.
   - **Memory**: unbounded caches; listeners never removed; large captures in closures.
   - **Concurrency**: blocking calls on the event loop or UI thread; locks held across IO; unbounded parallelism
     on a shared resource.
   - **Frontend**: work on every render; layout thrash; big bundles from a new dependency.
   - **Cost**: paid API or model calls per request; polling instead of events.
3. **Vet claimed numbers** with seven questions:
   1. What limits this number?
   2. Were both sides set up as in production?
   3. Is it physically plausible?
   4. Were there errors or wrong outputs during the run?
   5. Does it reproduce over alternating runs (median and range)?
   6. Does it matter end to end?
   7. Was the work actually inside the timed region?

   Verdict: faster / slower / no measurable difference / inconclusive.
4. **State the threshold.** Give the input size at which the problem starts to matter.

## Output

Findings (`category: performance`) with the size threshold, the fix, and (if feasible) a benchmark or query-count
test as the encode.

## Rules

- NEVER accept a single-run number as proof.
- NEVER flag micro-optimisations on cold paths.
- **Severity:**

  | Severity | When |
  |---|---|
  | MAJOR | O(n²) or N+1 on a path that grows with users or data; unbounded memory; blocking the main loop |
  | MINOR | wasteful but bounded work |

## Stop and ask

- Production data sizes are unknown and decide the severity. Ask.

## Next

Back to `tk-review`.
