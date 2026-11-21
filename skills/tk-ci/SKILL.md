---
name: tk-ci
description: Add Trust Kitchen's deterministic review to CI so every pull request is scanned and gated automatically - the diff scan and the merge gate run with tools, config and policy taken from the base branch (a PR cannot change its own judge), restricted areas are reported, a red verdict fails the check, and an optional job keeps one comment on the PR up to date for the owner. Least privilege, pinned actions. Use when asked "add review to CI", "run trust kitchen on every PR", "GitHub Action for review", or after tk-setup when the team wants automation.
---

# Review in CI

Machine checks belong in CI, where they run every time and nobody can forget them. This skill adds the
deterministic layer and the merge gate. Agent reviewers stay a separate, opt-in step.

## When to use

- The project has a CI system and wants every PR scanned and gated.
- Before turning on auto-merge. Auto-merge requires this.

Do not use it to give CI secrets to code from forks, or to auto-merge by itself.

## Inputs

- `.trust-kitchen/config.json` (commands, `restricted_paths`) and `.trust-kitchen/policy.json`, **as they are on
  the base branch**.
- The CI system in use. GitHub Actions is covered below; for other systems, apply the same rules.
- The template `references/github-workflow.yml` in this skill folder.

## Procedure

1. **Install Trust Kitchen on the base branch first.**
   - The workflow runs the scanner, the gate, the config and the policy **from the base branch**, never from the PR.
   - A PR that edits `.trust-kitchen/` therefore cannot switch its own review off. It is still tagged
     `review-config`, a restricted area.
2. **Copy the template** to `.github/workflows/trust-kitchen.yml`.
3. **Pin actions to a commit SHA.** Replace each `uses: owner/action@<PIN-TO-SHA>` with the full commit SHA of the
   release you reviewed (look it up on the action's release page). Never use a moving tag.
4. **Least privilege.**
   - The review job has `contents: read` only, and checks out with `persist-credentials: false`.
   - Only the optional comment job gets `pull-requests: write`.
   - Never use `pull_request_target` with a checkout of the PR head.
5. **Project checks.** Add the build, lint, type-check and test commands from `config.json` before "Scan and
   gate", running inside `pr/`. These are the strongest layer.
   - End them with `echo "TK_CHECKS=passed" >> "$GITHUB_ENV"`.
   - Without that line the gate sees the checks as missing and never says MERGE: nothing ran, so nothing is
     proven.
   - **Optional, for MERGE:** add a step that runs the real thing (end-to-end tests, or the project's
     `verify-<app>` skill as a script) and ends with `echo "TK_VERIFY=passed" >> "$GITHUB_ENV"`.
   - With checks and verify passed, a clean PR outside restricted areas gets **MERGE**. Without it, every code PR is
     NEEDS_HUMAN: the check is green and a person merges.
6. **What the check does:**
   - It runs from the workspace root with isolated Python (`python -I`). A file in the PR such as `json.py` cannot
     be imported by the tools.
   - The scanner ignores the PR's own `.gitattributes`, so a PR cannot hide its diff.
   - It scans the diff, builds the gate facts (`tk_ci_facts.py`) and runs `merge_gate.py`.
   - **Scanner MAJOR hits** are pattern matches (`setTimeout`, `# noqa`, `innerHTML`). With the default policy
     (`"ci_major_blocks": false`) they are shown for a person to confirm or dismiss, and never turn the check red on
     their own.
     - Set `"ci_major_blocks": true` in `policy.json` once the repository has measured few false alarms and the
       team uses the dismissal label below.
   - **BLOCKERs always turn it red:** a secret, a deleted or skipped test, prompt injection.
   - **Dismissing a false alarm:** a person with write or triage access adds the label **`tk:dismiss`** to the PR.
     - The run started by that label marks the scanner's BLOCKER / MAJOR findings "dismissed by @<who> for
       <commit>". They stop blocking, and the note appears in the job summary and the PR comment.
     - A new push needs a new dismissal: remove the label and add it again.
     - A dismissal never covers restricted areas or failing project checks.
   - **CHANGES_REQUESTED fails the check.**
   - **NEEDS_HUMAN passes the check**, but writes the reasons to the job summary. Examples: a restricted area, or
     behaviour CI cannot run. A person merges.
   - A scanner that could not run fails the check: "nothing was checked" is never green.
   - The verdict is uploaded as `verdict.json`. Anything that auto-merges must act only on `MERGE` from that file.
7. **Make it required.** In branch protection, mark the job as a required status check.
8. **Optional: show the result on the PR.**
   - The `comment` job keeps **one** comment on the PR up to date with the verdict and the findings. It is marked
     `<!-- trust-kitchen-review -->`, written by the Actions bot, and edited on every push. A comment with the same
     marker from anyone else is ignored.
   - It never approves or merges, runs no PR code, and skips fork PRs.
   - Every value from the diff is escaped, so a file name cannot inject links, mentions or HTML.
   - For the full agent review on a PR, use `tk-review-pr`.
9. **Optional agent review.** If the team runs an agent reviewer in CI, it must:
   - run on the PR's own code without repository secrets;
   - post findings only;
   - never merge.

   Keep it in a separate job and document it.
10. **Prove it bites.**
    - Open a test PR that adds a fake secret pattern and also edits `.trust-kitchen/scripts/tk_scan.py` to exit 0.
      The check must still fail.
    - Open a clean PR: the check passes.
    - Close both.

## Output

- `.github/workflows/trust-kitchen.yml` with pinned SHAs and least privilege.
- Proof: links to the failing test-PR run and the passing clean run.

## Rules

- NEVER run review tools, config or policy from the PR's own checkout.
- NEVER use `pull_request_target` together with checkout of the PR head.
- NEVER interpolate `${{ github.event.* }}` text into `run:` scripts. Pass it through environment variables.
- NEVER give a job write access it does not need.
- MUST pin third-party actions to a commit SHA.
- MUST treat a scanner error (exit 2) as a failed check.
- NEVER let a PR author dismiss their own findings. The `tk:dismiss` label needs write or triage access, which is
  why fork authors cannot use it. On a small team where the author is also an owner, write the reason in the PR.

## Stop and ask

- The repository is public and the owner wants agent review with secrets: explain the risk first.
- Branch protection settings need admin rights: the owner applies them.

## Next

`tk-merge-gate` (when auto-merge is considered) · `tk-eval` (measure before trusting) · `tk-review-pr` (full review
on a PR).
