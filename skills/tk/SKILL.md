---
name: tk
description: Trust Kitchen hub - start here, and the one command for everything. "/tk" alone shows where the project stands, one recommended next step and the menu. "/tk <command> [args]" runs the matching skill directly - "/tk review" (your changes), "/tk review 42" (pull request 42), "/tk code src/" (existing code), "/tk plan", "/tk setup", "/tk <any skill name>". Use when the user types "tk", "/tk ...", "trust kitchen", "what next", "help", "menu" or "status", or opens a project that has Trust Kitchen installed and gives no specific task.
argument-hint: "[command] [args] - e.g. review 42, code src/, plan, setup"
---

# Trust Kitchen hub

One entry point, used two ways:

- **`/tk`** (no command): one screen with where the project stands, the one thing to do next, and the menu.
  Read-only.
- **`/tk <command> [args]`**: run exactly the skill the command names, with the arguments, right away. No screen,
  no second question about which skill.

How each agent sends the words after `/tk` (they arrive as `ARGUMENTS:` or in place of the placeholder):

| Agent | Type |
|---|---|
| Claude Code, Cursor, GitHub Copilot, Kiro, Cline, Windsurf | `/tk review 42` |
| OpenAI Codex CLI | `$tk review 42` |
| Gemini CLI, OpenCode | `/tk review 42` (a small command file that loads this skill) |
| any other agent | "tk review 42" in plain words |

## When to use

- The user types `tk` or `/tk`, with or without a command.
- The user says "trust kitchen", "help", "menu", "what next" or "status".
- A session starts in a project with `.trust-kitchen/` and the user has no specific request yet.
- The user asks which skill does something.

If the user names a concrete task without `tk` ("review PR 42", "fix this bug"), go straight to the owning skill
(see the commands table).

## Inputs

**The arguments** (the words after `tk`). The first word is the command; the rest is passed on unchanged.

**The project state**, read only for the screen (no command). Each may be missing; a missing file is information,
not an error.

| Source | Read | If missing |
|---|---|---|
| `.trust-kitchen/` | whether Trust Kitchen is installed | not installed (step 1) |
| `.trust-kitchen/config.json` | written by `tk-setup` | setup missing (priority 0) |
| `.trust-kitchen/policy.json` | key `auto_merge` (true / false) | show "policy: missing (defaults: auto-merge off)" |
| `.trust-kitchen/state.md` | written by `tk-handoff`: sections `## Just done`, `## Next`, `## Waiting on` | show "(no state.md yet)" |
| ledger | `python .trust-kitchen/scripts/tk_ledger.py candidates` → `{"ledger": "present" or "missing", "candidates": [...]}` | the script reports `"ledger": "missing"` |
| git | `git branch --show-current`, `git status --short`, `git log -5 --oneline` | not a git repository (stop and ask) |

## Commands

The first word of the arguments, matched case-insensitively. A word that is not in the table but is a skill name,
with or without the `tk-` prefix (`/tk review-slop`, `/tk tk-limits`), runs that skill.

| Command | Skill | Arguments | Example |
|---|---|---|---|
| `status` | `tk` | none | `/tk status` (same as `/tk`) |
| `help` | `tk` | none | `/tk help` (the menu) |
| `setup` | `tk-setup` | none | `/tk setup` |
| `principles` | `tk-principles` | none | `/tk principles` |
| `plan` | `tk-plan` | the change, in words | `/tk plan add rate limiting` |
| `spec` | `tk-spec` | the feature | `/tk spec export to CSV` |
| `investigate` | `tk-investigate` | the symptom | `/tk investigate login fails on Safari` |
| `build` | `tk-build` | the approved plan or spec | `/tk build` |
| `pr` | `tk-pr` | none (opens / tidies your PR) | `/tk pr` |
| `ci` | `tk-ci` | none | `/tk ci` |
| `review` | `tk-review` | nothing (your changes), a branch, a diff file, or a PR number / URL | `/tk review 42` |
| `code` | `tk-review-code` | a folder, file or glob of existing code | `/tk code src/billing/` |
| `secure` | `tk-review-security` | same as `review` | `/tk secure 42` |
| `attack` | `tk-review-adversarial` | same as `review` | `/tk attack 42` |
| `verify` | `tk-review-verify` | same as `review` | `/tk verify` |
| `gate` | `tk-merge-gate` | a `facts.json` path, or nothing for the last review | `/tk gate` |
| `triage` | `tk-sec-finding-gate` | the finding | `/tk triage IDOR on /orders` |
| `net` | `tk-verify-network` | the command to watch | `/tk net npm test` |
| `supply` | `tk-skill-supply-chain` | the skill / plugin / MCP server | `/tk supply some-org/some-skill` |
| `harness` | `tk-create-verification` | none | `/tk harness` |
| `eval` | `tk-eval` | a cases folder, or nothing | `/tk eval` |
| `evidence` | `tk-evidence` | the claim | `/tk evidence tests pass` |
| `limits` | `tk-limits` | the limit | `/tk limits request timeout` |
| `contract` | `tk-worker-contract` | the agent or worker | `/tk contract release bot` |
| `retry` | `tk-error-taxonomy` | the failure | `/tk retry CI timed out` |
| `report` | `tk-report` | none | `/tk report` |
| `learn` | `tk-learn-rules` | nothing (uses the ledger), or the mistake | `/tk learn` |
| `handoff` | `tk-handoff` | none | `/tk handoff` |
| `chef` | `tk-head-chef` | none (role menu) | `/tk chef` |
| `cook` | `tk-sous-chef` | none (role menu) | `/tk cook` |
| `taster` | `tk-taster` | none (role menu) | `/tk taster` |
| `inspector` | `tk-inspector` | none (role menu) | `/tk inspector` |
| `expediter` | `tk-expediter` | none (role menu) | `/tk expediter` |
| `gardener` | `tk-gardener` | none (role menu) | `/tk gardener` |

`review` with a PR number or PR URL runs `tk-review` in **PR mode**, which hands the posting step to
`tk-review-pr`. Single-aspect reviewers have no short command; type their name, with or without `tk-`
(`/tk review-slop 42`):

| Reviewer | Looks at |
|---|---|
| `tk-review-deterministic` | the scanner and the project's own checks only |
| `tk-review-intent` | claim vs diff, business and user impact |
| `tk-review-architecture` | data model, boundaries, public API |
| `tk-review-slop` | code that hides problems instead of fixing them |
| `tk-review-tests` | whether tests prove the behaviour |
| `tk-review-blast-radius` | what breaks outside the diff |
| `tk-review-performance` | N+1, unbounded work, cost |
| `tk-review-data-migration` | schema, migrations, stored data |
| `tk-review-pr` | a GitHub PR, shown on the PR |

## Procedure

### A. With a command (`/tk <command> [args]`)

1. **Match** the first word against the Commands table, then against skill names (with or without `tk-`).
2. **No match:** say `Unknown command '<word>'.`, show the Menu block from the Output section, and stop. Never
   guess the closest command.
3. **Match:** load that skill's `SKILL.md` from the same skills folder as this file (for example
   `.claude/skills/tk-review/SKILL.md` or `.agents/skills/tk-review/SKILL.md`) and follow it **in full**, with
   the remaining arguments as its input. In agents with a skill tool, invoke the skill by name instead.
4. Everything that skill says still applies: its plan, approval and stop points. The command only saves the
   user from naming the skill; it never skips a gate.

### B. Without a command (`/tk`, `/tk status`, `/tk help`)

1. **Installed?** If `.trust-kitchen/` does not exist, show only this and **stop**:
   `Trust Kitchen is not installed here. Install: npx github:LilCheesy/Trust-Kitchen install`.
2. **Read every input** in the project-state table, using read-only commands.
3. **Choose exactly one next step.** Take the **first** rule that matches:

   | Priority | Condition | Next step |
   |---|---|---|
   | 0 | `config.json` missing | `/tk setup`: "review cannot run the project's own checks yet" |
   | 1 | `state.md` has a non-empty `## Waiting on` | remind the user of that decision; no skill |
   | 2 | `git status --short` shows changes | ask one question: "Review these changes (`/tk review`) or report finished work (`/tk report`)?" |
   | 3 | the ledger has candidates | `/tk learn`: "<n> mistakes repeated; turn them into checks" |
   | 4 | `state.md` has a `## Next` | that step, as a `/tk` command |
   | 5 | otherwise | "Pick from the menu" |

4. **Show the screen** (format below). Always show the menu. Lines stay under 100 characters; if the reason for
   the next step is long, put it on its own line.
5. **Wait.** Do not run the recommended step until the user types it or says "go".

## Output

Screen for `/tk` (procedure B):

```
TRUST KITCHEN · <project> · <branch>
Setup: done | missing          Policy: auto-merge off | on | missing (defaults)
Last: <first line of "Just done" in state.md, else last commit>   (<"no state.md yet" if missing>)
Waiting on you: <decision from state.md, or "nothing">

Next: /tk <command>
      <reason, one line>

Menu                                       type /tk <command> [args]
  START    setup        first-time setup          handoff     save state for next session
  PLAN     plan         four-line plan            spec        spec with acceptance criteria
  BUILD    investigate  root cause, read-only     build       red → green → clean
           pr           commits + PR body         ci          review in CI
  REVIEW   review       changes, or a PR: 42      code        existing code: src/
           attack       try to break it           gate        merge verdict
  PROVE    verify       run the real thing        harness     project verify skill
           eval         measure any skill
  SECURE   secure       security review           triage      triage a finding
           net          prove network egress      supply      vet a plugin / skill
  LEARN    learn        repeated mistakes → checks
  ROLES    chef  cook  taster  inspector  expediter  gardener
Any skill by name works too: /tk review-slop, /tk limits ...
```

With a command (procedure A): the chosen skill's own output, preceded by one line:
`→ tk-<skill> <arguments>`.

## Rules

- MUST dispatch `/tk <command>` to exactly the skill in the Commands table, and pass the rest of the arguments
  unchanged.
- MUST say "Unknown command" and show the menu when nothing matches. NEVER guess.
- NEVER let a command skip the target skill's approvals, plan or stop points.
- Without a command: MUST read the real state before recommending, recommend exactly one next step chosen by the
  priority table, and NEVER edit files or run the recommended step from the screen.
- NEVER report setup as done when `config.json` is missing.

## Stop and ask

- The directory is not a git repository: ask whether to continue without history.
- Priority 2 applies: ask the single question shown. Only the user knows whether the changes are finished work.
- An argument could mean two commands (for example a word that is both a command and a file name): ask which.

## Next

The skill the command named, or the recommended `/tk <command>` when the user says "go".
