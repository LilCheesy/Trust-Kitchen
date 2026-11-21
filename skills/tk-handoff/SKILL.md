---
name: tk-handoff
description: Save the session's state so the next session (or person) continues without re-discovering everything - what was just done, what is next, what is waiting on whom, open questions, and how to restart the environment. Use at the end of a session, before a long pause, or when asked "save state", "handoff", "where were we", "pick up where we left off".
---

# Handoff

Agents do not remember between sessions. The file is the memory.

## When to use

- At the end of every working session.
- Before a pause, a context reset, or handing the work to someone else.
- At the start of a session: read the file first.

Do not use it to store secrets, tokens or personal data. Never put them in the state file.

## Inputs

- What happened in this session: commits, files, results and decisions.
- `git status`, `git log`.
- The current plan or spec status.

## Procedure

### At the end of a session

1. Update `.trust-kitchen/state.md` with these sections:
   - **Just done**: what is finished, each item with its evidence (commit, test, command).
   - **Next**: the next concrete step, with the skill to run.
   - **Waiting on**: decisions or inputs pending, and from whom.
   - **Open questions**: numbered, each with a recommended answer.
   - **Restart**: the exact commands to bring the environment back.
   - **Log**: one line: date, what was done, result.
2. Keep it short. Replace stale lines; do not append forever. The log is the only part that grows.
3. If the team commits state, commit it on its own. Otherwise make sure the file is ignored by git.

### At the start of a session

1. Read `state.md`.
2. Check `git log` for changes since the last log line (someone else may have worked on it).
3. Write "session start, continuing from <item>" in the log.

## Output

```markdown
# State · <project> · updated <date>
## Just done
- <item> — evidence: <commit/test/command>
## Next
- <step> → run `<skill>`
## Waiting on
- <who>: <decision>
## Open questions
1. <question> (recommended: <answer>)
## Restart
<commands>
## Log
- <date> · <what> · <result>
```

## Rules

- NEVER write secrets, tokens, passwords or customer data into the state file.
- MUST include evidence for every "done" item.
- MUST distinguish done (proven) from done-but-not-proven.

## Stop and ask

- The state shows work that you did not do and cannot explain. Ask before continuing.

## Next

`tk` (the hub reads this file to recommend the next step).
