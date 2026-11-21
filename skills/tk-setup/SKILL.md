---
name: tk-setup
description: First-time setup of Trust Kitchen in a project - discover how the project builds, tests, lints and runs, record it in .trust-kitchen/config.json, choose the merge policy, and check that the review scripts work. Use right after installing, when the tk hub says setup is missing, or when asked "set up trust kitchen", "configure review", "init".
---

# Setup

The review is only as good as the checks it can run. Setup finds the project's real commands, so later skills do
not have to guess.

## When to use

- Right after install, or when `tk` reports "Setup: missing".
- After the project's toolchain changed (a new test runner, lint tool or build tool).

Do not use it to change the merge policy alone. Edit `.trust-kitchen/policy.json` and explain the change in a PR.

## Inputs

- The project root.
- Build and test files: `package.json`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `noxfile.py`, `Makefile`,
  `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `*.csproj`, `docker-compose*.yml`, `.github/workflows/*`,
  and the README.

## Procedure

1. **Detect the stack.** List the languages and frameworks you see, with the file that proves each one.
2. **Discover commands. Do not invent them.** For each of the following, find the exact command and the file it
   comes from:

   | Check | Examples of where to look |
   |---|---|
   | install | lockfile and package manager |
   | build | `scripts.build`, Makefile target, `go build` |
   | typecheck | `tsc --noEmit`, mypy / pyright config |
   | lint | eslint / ruff / golangci config |
   | test | `scripts.test`, pytest config, `go test ./...` |
   | run | the dev server or CLI entry point |

   If a check does not exist, record `null` and say so. "No linter" is useful information.
3. **Dry-run each command once.** Record the exit code and duration. Commands that fail on a clean checkout are
   recorded with `"status": "failing"`, not silently dropped.
4. **Find the default branch.** Use `git symbolic-ref refs/remotes/origin/HEAD`, or ask the user.
5. **Choose restricted areas.** Start from the built-ins (auth, security, migration, infra, ci, review-config,
   dependencies) and
   add project paths that need a person, such as `payments/` or `src/billing/`. They go into `restricted_paths`;
   the scanner reads them (`--config`) and tags matching files `restricted-path`, which the merge gate never
   auto-merges.
6. **Write `.trust-kitchen/config.json`:**

   ```json
   {
     "default_branch": "main",
     "commands": {"install": "...", "build": "...", "typecheck": null, "lint": "...", "test": "...", "run": "..."},
     "command_status": {"test": {"exit": 0, "seconds": 41}},
     "restricted_paths": ["payments/"]
   }
   ```

7. **Policy.** Keep `.trust-kitchen/policy.json` at `auto_merge: false` unless the owner explicitly asks
   otherwise. Explain the conditions for turning it on (see `tk-merge-gate`). A hard PR-size cap, if the team wants
   one, is `max_lines` in this file (none by default). Keep `ci_major_blocks: false` until the team has measured
   the scanner's false alarms on its own PRs (see `tk-ci`).
8. **Self-check the scripts:**

   ```
   python .trust-kitchen/scripts/tk_selfcheck.py
   ```

   - It plants a fake secret and known review facts, and checks that the scanner and the merge gate catch them.
     Every line must say OK. Report the output.
   - If `.trust-kitchen/scripts` is missing (for example after a plugin-only install), run the installer first:
     `npx github:LilCheesy/Trust-Kitchen install`.
9. **Offer next steps:**
   - `tk-create-verification` if the project can be run but has no way to prove behaviour;
   - `tk-ci` if the owner wants review on every PR.

## Output

```
Setup complete · <project>
Stack: <languages / frameworks (evidence file)>
Commands:  build ✔ 12s · typecheck — none · lint ✔ 4s · test ✖ failing on clean tree (3 tests) · run ✔
Restricted paths: <list>
Policy: auto-merge OFF
Self-check: scanner OK · merge gate OK
Next: <tk-create-verification | tk-ci | tk-plan>
```

## Rules

- NEVER invent a command. Every command must come from a project file or from the user.
- NEVER turn auto-merge on during setup.
- NEVER "fix" a failing test or lint during setup. Record it; fixing it is a separate, planned change.
- MUST record missing checks as `null`, not leave them out.

## Stop and ask

- No default branch can be determined.
- A command needs secrets, production access or paid services to run.
- The test suite takes longer than 10 minutes. Ask which subset to use for review.

## Next

`tk-create-verification` · `tk-ci` · `tk` (to see the menu)
