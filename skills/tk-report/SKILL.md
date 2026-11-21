---
name: tk-report
description: Report finished work in six parts so the owner can verify it in minutes instead of trusting it - what is done (proven / not proven / not done), how far, cases checked and not checked, how to verify and how to break it, how sure, where it may be wrong - plus files changed and commit status. Use at the end of every task, PR or review, and whenever you would say "done", "fixed", "works", "all green".
---

# Six-part report

"Done" is a claim. A report is something the owner can check.

## When to use

- At the end of every task, PR, review or session.
- Whenever you are about to write "done", "fixed", "works" or "all green".

Do not use it to summarise reading or research that changed nothing. A short answer is enough there.

## Inputs

- The plan or spec and its acceptance checks.
- The evidence collected (`tk-evidence`).
- The list of files changed, and the commit and push status.

## Procedure

1. **What is done.** One line per item:
   - ✅ proven, with the check and its evidence level;
   - 🟡 done but not proven, with the reason;
   - ⬜ not done, with the reason.
2. **How far.** Give `x / y` for criteria, files and tests.
3. **Cases checked.** List the normal, edge and failure cases, **and the cases not checked**.
4. **How the owner can check it.**
   - The exact command and the output they should see.
   - What to look at by eye, and the value they should expect.
   - **How to break it**: one edit that must turn a named test red.
5. **How sure.** Rate each important claim high, medium or low, and say why.
6. **Where it may be wrong.** At least one line, with the symptom that would show it.
7. **Files changed.** One line each, `file:line` and one sentence. Then say whether it is committed or pushed.

## Output

```
✅ <item> — proven by <check> (level n)
🟡 <item> — not proven because <reason>
⬜ <item> — not done because <reason>
Progress: <x/y criteria> · <files> · <tests>
Checked: <cases> · Not checked: <cases>
Verify yourself: <command> → expect <output> · Break it: change <x> → <test> must fail
How sure: <claim: level, why>
May be wrong: <where> · Symptom: <what you'd see>
Files: <file:line — what> …
Committed: <sha, branch> | not committed · Pushed: yes/no
```

## Rules

- NEVER use "done", "complete", "works", "fixed", "all good" or "checked" without the evidence next to it.
- MUST include the "not checked" list, even if it is short.
- MUST include a way to break it, for every behaviour claim.
- If you reported something wrong earlier, correct it at the top: "Earlier I said X; it is Y, because Z." Never
  fix it silently.

## Stop and ask

- You cannot give a way to verify a claim. Downgrade the claim to 🟡 and ask what evidence the owner wants.

## Diagrams (when they help)

Draw one when the report has a flow, a structure or a before / after that words make slow to follow. Use Mermaid,
so the diagram lives in the text and can be reviewed in a diff.

- **Boxes:** every box has two lines, a plain name in bold and the code identifier:
  `A("<b>Merge gate</b><br/><code>merge_gate.py</code>")`.
- **The border shows state:**
  - solid dark green = main / exists;
  - dashed grey = not built yet / secondary;
  - dashed orange = assumption;
  - solid thick orange = **you are here** (the part this work changed);
  - red = risk or forbidden.
- **Arrows** carry a short label of what moves or why: `A -- "findings" --> B`. A forbidden path is a red dashed
  arrow, styled with `linkStyle`.
- **The main flow** goes left to right (`flowchart LR`).
- **Under the diagram**, one sentence: "This shows …", and the conclusion the reader should take away.
- **The diagram must match the code as it is now.** Every box with an identifier names something that exists, or
  is drawn as not built. A diagram that disagrees with the code is a bug in the report.
- **Say where to see it:** the file and section, and what renders it (GitHub renders Mermaid; VS Code needs a
  Mermaid preview extension).

Styles to paste:

```mermaid
flowchart LR
    classDef main fill:#ffffff,stroke:#1f7a4d,stroke-width:2.5px,color:#1b232c
    classDef planned fill:#ffffff,stroke:#8a939c,stroke-width:1.5px,stroke-dasharray:6 4,color:#1b232c
    classDef assumed fill:#ffffff,stroke:#d9822b,stroke-width:1.5px,stroke-dasharray:6 4,color:#1b232c
    classDef here fill:#fff4e6,stroke:#d9822b,stroke-width:3px,color:#1b232c
    classDef risk fill:#fff0f0,stroke:#c62828,stroke-width:2px,color:#1b232c
```

## Next

`tk-handoff` (save state) · `tk` (next step).
