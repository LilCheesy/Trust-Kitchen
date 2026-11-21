<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
    <img alt="Trust Kitchen" src="assets/banner-light.svg" width="640">
  </picture>
</p>

<h3 align="center">Ship fast. Prove it.</h3>

<p align="center">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0E9F7E">
  <img alt="skills" src="https://img.shields.io/badge/skills-42-0E9F7E">
  <img alt="agents" src="https://img.shields.io/badge/agents-9-0E9F7E">
  <img alt="install" src="https://img.shields.io/badge/install-npx%20%7C%20python-0E9F7E">
  <img alt="python" src="https://img.shields.io/badge/python-3.10%2B-0E9F7E">
  <img alt="node" src="https://img.shields.io/badge/node-18%2B-0E9F7E">
</p>

---

Skills that make agent-assisted engineering trustworthy: plan before changing, prove before claiming, review every
change with focused parallel reviewers and a testable merge gate, and turn every repeated mistake into a machine
check. Plain `SKILL.md` folders — they work in any agent that reads skills, and in the rest through `AGENTS.md`.

## Installation

### One command (Node 18+)

Run inside your project:

```bash
npx github:LilCheesy/Trust-Kitchen install
```

The installer asks which agents you use and writes the skills where each one looks for them. Non-interactive:

```bash
npx github:LilCheesy/Trust-Kitchen install --agents claude-code,codex,cursor --yes
```

### Without Node (Python 3.10+)

```bash
git clone https://github.com/LilCheesy/Trust-Kitchen.git
python Trust-Kitchen/installer/install.py install --dir path/to/your/project --agents claude-code,codex
```

### Claude Code plugin (skills only)

```bash
claude plugin marketplace add LilCheesy/Trust-Kitchen
claude plugin install trust-kitchen@trust-kitchen
```

The plugin brings the skills, namespaced as `/trust-kitchen:tk`. It does not add the review scripts or the policy to
your project, so run the installer above once as well (`npx github:LilCheesy/Trust-Kitchen install --agents
claude-code`); `/trust-kitchen:tk setup` reminds you if they are missing.

### Where things go

| Agent | Skills | Type | Also |
|---|---|---|---|
| Claude Code | `.claude/skills/` | `/tk review 42` | reviewer subagent in `.claude/agents/` |
| OpenAI Codex CLI | `.agents/skills/` | `$tk review 42` | `AGENTS.md` |
| Cursor | `.agents/skills/` | `/tk review 42` | `AGENTS.md` |
| Gemini CLI | `.agents/skills/` | `/tk review 42` | `.gemini/commands/tk.toml`, `GEMINI.md`, `AGENTS.md` |
| Windsurf / Devin | `.agents/skills/` | `/tk review 42` | `AGENTS.md` |
| GitHub Copilot | `.github/skills/` | `/tk review 42` | `.github/copilot-instructions.md`, `AGENTS.md` |
| Cline | `.cline/skills/` ¹ | `/tk review 42` | `.clinerules/trust-kitchen.md`, `AGENTS.md` |
| Kiro | `.kiro/skills/` ¹ | `/tk review 42` | `.kiro/steering/trust-kitchen.md`, `AGENTS.md` |
| OpenCode | `.agents/skills/` | `/tk review 42` | `.opencode/commands/tk.md`, `AGENTS.md` |

¹ Skill folder not yet confirmed in that agent's own documentation. The rule file always points the agent at the
skills, so plain-language requests ("tk review 42") work either way.

Every install also adds the review scripts to `.trust-kitchen/scripts/`, the eval runner to `.trust-kitchen/evals/`,
and a default merge policy (auto-merge off) to `.trust-kitchen/policy.json`.

- **Your files are safe.** A file Trust Kitchen did not write is never overwritten: it is skipped and reported. Rule
  files change only inside a marked `trust-kitchen` block.
- **Uninstall removes exactly what was installed**, except files you changed after installing (an edited
  `policy.json`, for example). Those are kept and listed.

### Update, status, uninstall

```bash
npx github:LilCheesy/Trust-Kitchen update       # re-install for the same agents
npx github:LilCheesy/Trust-Kitchen status
npx github:LilCheesy/Trust-Kitchen uninstall    # removes what was installed, keeps what you edited
```

The same commands work with `python installer/install.py <command> --dir <project>`. Pin to a release you have
read before using it in a team (see `tk-skill-supply-chain`).

### First run

Open your agent in the project and type `/tk`. The first time, it sends you to `/tk setup`, which finds your
build, lint and test commands and checks that the review scripts work.

## Using it: one command

Everything starts with `/tk` (`$tk` in Codex). Without a command it shows where the project stands, the next step
and the menu. With a command it runs that skill straight away:

```text
/tk                      status, next step, menu
/tk setup                first-time setup
/tk plan add rate limits four-line plan, then wait for approval
/tk build                red → green → clean, inside the approved files
/tk review               review your local changes
/tk review 42            review pull request 42 and, after you say yes, show it on the PR
/tk code src/billing/    review existing code and rank the fixes worth doing first
/tk secure 42            security review only
/tk learn                turn repeated mistakes into checks
/tk review-slop          any skill works by name, with or without "tk-"
```

Reviews on a pull request are posted as a **comment**, never as an approval: the repository owner reads them and
decides what gets merged.

## Skills

### Start here

| Skill | What it does |
|---|---|
| `tk` | The hub and the one command. `/tk` reads the project state, recommends one next step and shows the menu; `/tk <command> [args]` runs the matching skill directly. |
| `tk-setup` | First-time setup: discovers build / typecheck / lint / test / run commands, records them, sets restricted paths (enforced by the scanner and the merge gate), keeps auto-merge off, and proves the scripts catch a planted problem. |

### Roles

Each role greets you with a menu of codes and routes them to the skills below.

| Skill | Role | Menu |
|---|---|---|
| `tk-head-chef` | Plans and coordinates: restates the goal, sizes the work, slices it into verifiable steps, assigns roles, tracks status. | `PLAN` `SPEC` `SLICE` `STATUS` `HANDOFF` |
| `tk-sous-chef` | Builds: investigates first, red test, smallest green change, clean up, PR. Never reviews its own work. | `INVEST` `BUILD` `PR` `REPORT` |
| `tk-taster` | Proves behaviour by running the real thing; keeps the verification skill; measures every skill. | `VERIFY` `NET` `HARNESS` `EVAL` |
| `tk-inspector` | Defensive security: reviews code, gates findings, checks network egress, vets third-party skills. | `SECURE` `GATE` `NET` `SUPPLY` |
| `tk-expediter` | Decides what ships: full review, PR review shown on the PR, existing-code review, adversarial pass, merge gate verdict. | `REVIEW` `PR` `CODE` `ATTACK` `GATE` `CI` |
| `tk-gardener` | Turns repeated mistakes into machine rules and keeps session state. | `LEARN` `RULES` `HANDOFF` |

### Foundation

| Skill | What it does |
|---|---|
| `tk-principles` | The seven working rules every skill assumes: the trust stack, evidence before claims, the author never grades their own work, every correction becomes a rule, small reversible steps, honest numbers, trust before parallelism. |
| `tk-plan` | Four lines before any change (will do, files, how to check, needs you), explicit approval, and the eight stop points. |
| `tk-evidence` | Evidence levels 0–5 for claims, confidence 1–5 for findings, MEASURED / COMMANDED / ASSUMED labels, "inconclusive" instead of guessing, redaction. |
| `tk-limits` | Every limit declared with owner, value, unit, meaning, source and kind; assumed limits are never called safe. |
| `tk-worker-contract` | Roles, task contract, LOW / HIGH / FORBIDDEN actions, no self-approval, machine score separate from acceptance, explicit sensitive-data access, audit. |
| `tk-error-taxonomy` | Seven failure classes and a retry rule: retry only when nothing has happened yet. |
| `tk-report` | Six-part completion report with how to verify, how to break it, and where it may be wrong. |
| `tk-learn-rules` | Repeated mistakes become the strongest enforceable rule (type, lint, CI, test), proven against the old mistake and proposed as its own PR. |
| `tk-handoff` | Saves just done / next / waiting on / open questions / restart commands so the next session continues. |

### Build

| Skill | What it does |
|---|---|
| `tk-spec` | Spec before code: context, current state with evidence, agent contract, scope, behaviour, edge cases, acceptance criteria with named tests, limits, file list, test plan. |
| `tk-investigate` | Read-only root-cause analysis: reproduce, trace to the first wrong place, test hypotheses, report the fix direction. |
| `tk-build` | Red → green → clean in small steps inside the approved files, with self-scan and the project's checks. |
| `tk-pr` | Small logical commits and a one-minute PR body: what and why, changes, evidence, risk, rollback, not tested. |
| `tk-ci` | Adds the deterministic review and the merge gate to CI, run with tools and policy from the base branch so a PR cannot change its own judge; pinned actions, least privilege, an optional single comment on the PR; owners dismiss false alarms with a `tk:dismiss` label; a clean, checked and verified PR reaches MERGE; proves it fails on a bad PR. |
| `tk-create-verification` | Creates a project `verify-<app>` skill (launch, doctor, drive, evidence, cleanup, feature map) and proves it works and can fail. |

### Review

| Skill | What it does |
|---|---|
| `tk-review` | Entry point: deterministic checks, relevant reviewers in parallel (each fresh), merged proven findings, merge-gate verdict, one-minute report, ledger record. |
| `tk-review-pr` | Reviews a GitHub pull request by number or URL with the full review, then, after you say yes, posts one review on the PR (summary + inline comments) as a comment only. Never approves or merges: the repository owner decides. |
| `tk-review-code` | Reviews existing code (a folder, module or file) with the same reviewers and proof rules, and ranks the five fixes worth doing first. Read-only. |
| `tk-review-deterministic` | Diff scanner (secrets, weakened tests, suppressions, symptom fixes, excuse comments, debug leftovers, dangerous calls, prompt injection, dependencies, size, restricted areas) plus the project's own checks. |
| `tk-review-intent` | Product and business view: claim vs diff, hidden behaviour changes, acceptance criteria, user impact, business edges, rollout, rollback, cost. |
| `tk-review-architecture` | Data model, impossible states, one owner per state, boundaries, public API, needless layers, migration discipline, idempotency. |
| `tk-review-slop` | Code that hides problems instead of fixing them: symptom fixes, swallowed errors, impossible-state guards, excuse comments, suppressions, copy-paste, dead weight, fake completeness. |
| `tk-review-tests` | Whether tests prove behaviour and whether the safety net was weakened: fail-without-the-change, behaviour over implementation, edges, mocks, determinism. |
| `tk-review-security` | Defensive security review with ten checklists (injection, access control, auth and tokens, SSRF, files and deserialisation, browser, secrets and data, supply chain and infra, LLM and agents, business logic and races), CVSS scoring, sandbox proof. |
| `tk-review-blast-radius` | What breaks outside the diff, and proof of the one fact the change's safety depends on. |
| `tk-review-verify` | Runs the real thing in isolation, compares with the base, returns passed / failed / inconclusive with artifacts. |
| `tk-review-performance` | N+1, unbounded work, quadratic loops, blocking calls, memory growth, cost per request; vets performance claims. |
| `tk-review-data-migration` | Existing data, locking, idempotency, rollback, contract compatibility, personal data. |
| `tk-review-adversarial` | Independent adversaries try to break the change; only reproduced findings survive. |
| `tk-merge-gate` | Fixed, tested merge policy; restricted areas always need a person; auto-merge only on opt-in. |

### Security

| Skill | What it does |
|---|---|
| `tk-sec-finding-gate` | Seven questions every security finding must pass before it may block; downgrade instead of escalate. |
| `tk-verify-network` | Allowlist first, canary secret, sandboxed run with packet capture, scripted check of every destination. |
| `tk-skill-supply-chain` | Vets third-party skills, plugins and MCP servers: pin, tripwire scan, read, list permissions, run isolated, decide. |

### Measure

| Skill | What it does |
|---|---|
| `tk-eval` | Unit tests for skills: measures any skill on cases written in advance (catch rate and false alarms for reviewers, a rubric for the rest), with blind copies, a second judge from another model, a tune set climbed to 10/10 and a holdout set for the honest number. |

### Subagent

| Agent | What it does |
|---|---|
| `tk-reviewer` | Fresh, narrow reviewer that `tk-review` spawns for each parallel reviewer (Claude Code). |

## License

MIT
