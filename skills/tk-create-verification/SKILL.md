---
name: tk-create-verification
description: Create a project-specific verification skill (verify-<app>) that tells any agent exactly how to launch the app, check it is healthy, drive its features, collect evidence and clean up - then prove the new skill works end to end once. Use after tk-setup when the project can run, or when asked "make the agent able to test the app", "create a verify skill", "how do we prove changes work here".
---

# Create a verification skill

The fastest way to trust agent work is to let the agent run the product the way a user would. Do it the same way
every time, with evidence.

## When to use

- The project has something runnable (a CLI, a service, a UI, a job) and reviews keep ending in "inconclusive".
- A new feature area appears that the existing verify skill does not cover.

Do not use it for pure libraries. Targeted tests are the verification there.

## Inputs

- `.trust-kitchen/config.json` (the run command).
- The README, scripts, docker-compose and env examples.
- The main user-facing features (ask the owner if they are unclear).

## Procedure

1. **Launch.** Find the exact command that starts the app in a clean environment, with test configuration and no
   production secrets. Write down the ports, the seed data and how long start-up takes.
2. **Doctor.** Write a health check that tells "the app is up and ready" apart from "the process started".
3. **Drive.** Pick the cheapest reliable driver:

   | App type | Driver |
   |---|---|
   | CLI | real command invocation |
   | HTTP API | requests against the running service |
   | web UI | browser automation |
   | terminal UI | pseudo-terminal |

   Prefer a small project CLI with composable commands, JSON output and clear errors over long ad-hoc scripts.
4. **Feature map.** List each user-facing feature with the exact steps to drive it and what to observe. For each
   feature, also record:
   - the names users actually use, including vague ones ("the left sidebar", "the export thing"). The map is a
     shared vocabulary that turns a vague report or a screenshot into a place in the app;
   - the entry path from launch and its sub-features;
   - keyboard shortcuts;
   - stable selectors or IDs the driver uses.

   Also write a small **maintain** procedure in the skill: when a feature is added, renamed or moved, update its
   map entry in the same change.
5. **Evidence.** For each feature, say what proves it worked: output lines, a stored value read back, a screenshot,
   a trace. Store artifacts in a temporary folder and hash them.
6. **Cleanup.** Stop processes, remove temporary data, and free ports. Running it twice must work.
7. **Write the skill** at `<skills dir>/verify-<app>/SKILL.md`, using the Trust Kitchen frame (When to use,
   Inputs, Procedure with Launch / Doctor / Drive / Evidence / Cleanup, Output, Rules, Stop and ask, Next).
8. **Prove the skill once.** Run it from a clean checkout on one real feature, and paste the evidence. **If this
   proof fails, do not ship the skill.**
   - Do the first runs **locally, and watch the agent drive the app** step by step before anyone uses the skill
     unattended or in the cloud.
   - Failures you watch become skill fixes.
9. **Prove it can fail.** Break that feature in a scratch branch. The skill must report `failed`.

## Output

The `verify-<app>` skill folder (and a project CLI if you created one), plus the proof run: the passing run and
the failing run on the deliberately broken feature.

## Rules

- NEVER use production data or real credentials in the verify skill.
- MUST make cleanup idempotent.
- MUST prove the skill works and can fail before anyone relies on it.
- MUST keep the feature map in step with the code. Update it when features change.

## Stop and ask

- Launch needs paid services, hardware or secrets that the agent should not have.
- The owner has not said which features matter most.

## Next

`tk-review-verify` uses the new skill · `tk-ci` can run its smoke subset.
