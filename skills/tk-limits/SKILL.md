---
name: tk-limits
description: Declare every limit (speed, force, time, size, rate, threshold, quota) with owner, value, unit, real-world meaning, source, source kind (vendor / measured / team / assumed), user, what happens when exceeded and knock-on effects - and never call anything safe when its limit is an assumption. Use when code, configs, specs or reports introduce or rely on a limit, or when asked "where does this number come from", "is this safe".
---

# Limits

A limit nobody can trace is a guess wearing a uniform.

## When to use

- A spec, config or code change introduces or changes a limit, threshold, quota, timeout or rate.
- A report concludes "within limits" or "safe".
- A review finds a magic number that guards something important.

Do not use it for ordinary constants with no safety, cost or contract meaning (loop counters, padding).

## Inputs

- The limit and where it is used.
- Its source documents: vendor datasheet, measurement log, or team decision record.

## Procedure

1. **Find every limit** in scope: search the configs and code for thresholds, timeouts, max and min values,
   rates and quotas.
2. **Declare each one** with eight fields:

   | Field | Example |
   |---|---|
   | Belongs to | checkout API · upload API · tenant disk quota |
   | Value + unit | 2 s p95 · 20 GB · 400 lines |
   | Real-world meaning | 180°/s, about half a turn per second |
   | Source | vendor datasheet p. 6 · team decision 2026-10-15 · measured on unit #3 |
   | Kind | **VENDOR** · **MEASURED** · **TEAM** · **ASSUMED** |
   | Used by | `file:function` that enforces or reads it |
   | When exceeded | reject · stop · warn · log only |
   | Knock-on effects | what else changes if this value changes |

3. **Check object match.** A limit belongs to one object. A motor's limit does not apply to another motor, and one
   tenant's quota is not another's. Verify that the config being used describes the thing being judged.
4. **Judge only sourced limits.** Values with no source are **measured and shown, but not judged**, and the report
   says so explicitly.
5. **Single source of truth.** Code reads the limit from its config at run time. Flag any second copy of the
   number.

## Output

A limits table (the eight fields), plus a list headed "Not judged (no source)".

## Rules

- NEVER call an ASSUMED limit "safe". Write "within the assumed limit, not verified".
- NEVER invent a limit. With no source, mark it ASSUMED and ask the owner.
- NEVER copy a limit across objects without checking that the source covers both.
- MUST show the limit next to the measured value (current and peak).

## Stop and ask

- A limit is needed but has no source. The owner decides the value and its kind.
- A vendor value and a team value disagree.

## Next

`tk-spec` (limits section) · `tk-review-verify` (measure against the limits).
