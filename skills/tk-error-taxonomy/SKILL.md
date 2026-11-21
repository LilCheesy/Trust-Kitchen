---
name: tk-error-taxonomy
description: Classify every failed run by who is responsible (infrastructure, capacity, timeout, input, the job itself, policy, orchestrator) and allow a retry only when nothing has happened yet. Use when a job, tool call, test run, deployment or agent step fails, when designing retry logic, or when asked "should we retry", "why did it fail", "error class".
---

# Error taxonomy

Retrying the wrong failure turns one bug into two side effects.

## When to use

- Any failed run of a job, test, deploy, tool call or agent step.
- When writing or reviewing retry logic.

Do not use it to excuse a bug ("it was flaky"). A flaky failure is still a finding.

## Inputs

- The failure: exit code, error message, logs, and how far the job got.

## Procedure

1. **Find how far it got.** Did the job start? Did it write anything (files, DB rows, messages, payments)?
2. **Classify:**

   | Class | Meaning | Example | Retry? |
   |---|---|---|---|
   | `START_FAILED` | Infrastructure failed **before** the job did anything | container failed to start, image missing | yes, bounded (≤ 2) |
   | `NO_CAPACITY` | Queue or resources full | HTTP 429, all slots busy | later, with backoff |
   | `TIMEOUT` | Ran too long and was killed | time limit | no; partial work may exist |
   | `USER_INPUT` | Bad parameters | invalid argument | no; fix the input |
   | `JOB_ERROR` | The job's own code failed | non-zero exit, exception, OOM | no; it is a bug or a limit |
   | `POLICY_DENY` | A rule refused it | tool not allowed, quota | no; never route around it |
   | `INTERNAL` | The orchestrator itself failed | monitor or collector crashed | no; escalate |

3. **Decide on a retry.** Retry only `START_FAILED` and `NO_CAPACITY`, and only when step 1 showed nothing was
   written.
4. **Record it.** Store the class, the exit code, a one-line reason and how far the job got, next to the run.
5. **Make operations idempotent** where possible, so that a partial run followed by a rerun reaches the same end
   state.

## Output

`class · exit · reason · progress (nothing / partial: <what> / complete) · retry: yes (n of 2) | no`

## Rules

- NEVER retry after a job may have produced side effects.
- NEVER work around `POLICY_DENY`. Report it.
- NEVER record a failure as just "failed" without a class.
- MUST keep a failure inside one job from taking the runner down.

## Stop and ask

- A `TIMEOUT` or `JOB_ERROR` left partial writes. The owner decides on cleanup.
- `INTERNAL` errors repeat.

## Next

`tk-investigate` (for `JOB_ERROR`) · `tk-report`.
