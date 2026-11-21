---
name: tk-evidence
description: Attach evidence and an evidence level to every claim, finding and "done" - evidence levels 0-5 for claims, confidence 1-5 for review findings, MEASURED / COMMANDED / ASSUMED labels for numbers, "inconclusive" instead of guessing, and redaction of secrets and personal data. Use whenever you report a result, a bug, a review finding or a status, or when asked "prove it", "how sure are you", "is it really done".
---

# Evidence

If it is not shown, it did not happen.

## When to use

- Whenever you claim something works, is fixed, is done, is safe, is slower or faster.
- In every review finding.
- When someone asks how sure you are.

Do not use it to pad reports. Evidence is the shortest artifact that proves the claim.

## Inputs

- The claim, and the commands, outputs or observations behind it.

## Procedure

1. **State the claim** in one sentence.
2. **Attach the artifact.** Paste the exact command and the relevant output lines; or give `file:line`; or a
   screenshot path with its hash.
3. **Assign the level.**

   **Evidence levels for claims about the system:**

   | Level | You did | Enough for |
   |---|---|---|
   | 0 | Said it | nothing |
   | 1 | Read code, cite `file:line` | wiring, structure |
   | 2 | Ran it locally (command + output) | an intermediate step |
   | 3 | Ran it in a clean environment (fresh clone or CI) | **minimum for "done"** |
   | 4 | Ran the whole system and measured it | conclusions about system behaviour |
   | 5 | Real hardware or production | conclusions about real-world safety |

   **Confidence for review findings:**

   | Confidence | Meaning | May block a merge? |
   |---|---|---|
   | 1 | "I think", no pointer | no |
   | 2 | Points at `file:line` or library source | no |
   | 3 | Traced the failing path and showed it is reachable | yes |
   | 4 | Ran a script or test against the real code and it fails | yes |
   | 5 | Reproduced in the running application | yes |

4. **Chain rule.** A conclusion takes the **lowest** level in its chain.
5. **Label numbers.**
   - **MEASURED**: from a sensor or real state.
   - **COMMANDED**: what was asked for.
   - **ASSUMED**: not measured.
   - **GROUND TRUTH**: used only for scoring.

   Show the limit next to the value, with the current value and the peak. Missing data is **NO DATA**, never 0.
6. **Redact.** Never paste secrets, tokens, cookies, passwords or personal data. Show a masked hint instead, for
   example `AKIA…(20 chars)`.

## Output

```
Claim: <one sentence>
Evidence: <command>  →  <output excerpt>   | <file:line> | <artifact path + sha256>
Level: <0–5> (<why not higher>)
```

## Rules

- NEVER invent a command, flag, file or output. If you did not check, say "not checked".
- NEVER call something done below level 3.
- NEVER call "correct in simulation" "safe".
- MUST check the real target, not a stand-in (the right config, the right device, the right service).
- MUST separate observed facts, assumptions, and what another agent told you.
- MUST ground every stated cause in something actually read or run in this session: the `file:line` you opened,
  the command you ran. A cause named for a file you never opened is a guess. Label it "hypothesis" and go look.
- MUST suspect the measurement before the system when a result is strange.

## Stop and ask

- The only available evidence would require production data, secrets or hardware access.
- A result is too good to be true (100 %, zero errors, ten times faster). Exception: a `tk-eval` tune set at 10/10
  is the goal; a perfect holdout score is not.

## Next

`tk-report` (to present the evidence) · `tk-review-verify` (to produce runtime evidence).
