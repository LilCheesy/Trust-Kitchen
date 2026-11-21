---
name: tk-review-verify
description: Verify a change by running the real thing - targeted tests, the CLI, the service or the app - in isolation, compared with the base version, and return passed / failed / inconclusive with commands, outputs and artifacts, never a guess. Use as a tk-review reviewer when behaviour changed, or when asked "does it actually work", "run it", "verify this change", "show me proof".
---

# Runtime verification

"It compiles" and "the code looks right" are not evidence of behaviour. An artifact beats a plausible explanation.

## When to use

- Behaviour changed and the project can be run or tested.
- Someone claims "it works" without evidence.

Do not use it for documentation-only changes (`verify: not_applicable`).

## Inputs

- The change (branch or diff) and its claimed behaviour.
- `.trust-kitchen/config.json` (run and test commands).
- The project's `verify-<app>` skill, if it exists (`tk-create-verification`).

## Procedure

1. **Find how it runs.** Prefer the project's verify skill. Otherwise use the config, the README and the scripts.
2. **Pick the check that matches the change:**

   | Change | Check |
   |---|---|
   | library / function | targeted tests, or a scratch script calling it with the risky inputs |
   | CLI | real command with realistic arguments; compare output before and after |
   | HTTP / API | start the service; call the endpoint; check status, body and side effects |
   | UI | drive the flow; take screenshots before and after |
   | data / migration | run on a copy; read the stored values back |
   | performance | measure before and after on the same machine; report median and range |

3. **Isolate.** Use a sandbox, container or temporary directory, test configuration, no production credentials,
   and no network unless the change needs it (`tk-verify-network`).
4. **Compare with the base.** Run the same check on the base commit to show the behaviour really changed, in the
   intended way.
5. **Collect evidence.** Keep commands, output excerpts and artifact paths with their hashes. Keep the artifacts
   local.
6. **Verdict.**
   - `passed`: the evidence shows the intended behaviour.
   - `failed`: the evidence shows wrong behaviour. Add a finding (`category: verify`).
   - `inconclusive`: it cannot be run here. Say what would be needed.

## Output

```
verify: passed | failed | inconclusive
- <command>  →  <key output lines>     (base: <output on base>)
artifacts: <path · sha256>
not verified: <what, why>
```

## Rules

- NEVER mark `passed` on reasoning alone.
- NEVER read `passed` as "good code". A passing run proves the behaviour is **correct**, not that the code is
  **good**. It never replaces the slop, architecture or tests review, and never lets them be skipped.
- NEVER use production data or credentials.
- NEVER change the code under review to make it pass.
- MUST label simulated or mocked runs as such. Simulation is not reality.

## Stop and ask

- Verification needs secrets, paid services, hardware or production access.
- The result is surprising (too good, too fast, very different from last time).

## Next

Back to `tk-review` (the verify field of the facts).
