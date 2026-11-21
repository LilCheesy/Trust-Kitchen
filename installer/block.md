## Trust Kitchen

This project uses the Trust Kitchen skills. Skills are in: {skills_dirs}.

- Start with the `tk` skill: it reads the project state and tells you the next step and the command for it.
- First time in this project: run `tk-setup`.
- Before any change, follow `tk-plan`. Before calling work done, follow `tk-report`.
- Review a change with `tk-review`. Never approve or merge your own work.
- Scripts used by the skills are in `.trust-kitchen/scripts/` (Python 3.10+, standard library only).

If your tool does not load skills automatically, open the skill's `SKILL.md` file from the folder above and follow it.
