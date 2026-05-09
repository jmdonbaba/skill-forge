# skill-forge project

Distill winding agent task completions into reusable, environment-aware Claude Code skills.

## What this project does

- Defines a meta-skill (`SKILL.md`) that teaches Claude Code how to generate new skills from completed task experiences
- Provides a Python script (`scripts/generate.py`) for standalone skill generation
- Includes real-world examples from Windows + China network environments
- Captures environment-specific context (OS, shell, proxy, tool versions) in each generated skill

## Project context

Claude Code skills live in `~/.claude/skills/`. Each skill is a `.md` file with frontmatter. The meta-skill defined here (`SKILL.md`) gets installed there via `scripts/install.sh`.

When a user invokes `/skill-forge`, Claude:
1. Asks about the task that was just completed (what, failures, success, environment)
2. Generates a skill file using the template at `templates/skill-template.md`
3. Saves the generated skill to `~/.claude/skills/{name}.md`

## Key design decisions

- **Environment-first**: Every skill records OS, shell, network constraints. Generic skills are useless in edge-case environments.
- **Pitfalls before solutions**: Recording what *didn't* work is more valuable than what did — it prevents repeating the same dead ends.
- **Verified commands only**: Never generate placeholder commands. Every command in a skill must be one that actually ran successfully.
- **Keep skills focused**: One skill = one task domain. Resist the urge to make a "general tips" skill.

## Adding examples

Place new examples in `examples/`. Each example is a complete skill file showing what the finished output looks like. Name them descriptively (e.g., `docker-push-china.md`, `npm-install-proxy.md`).

Good examples include:
- 2+ failed approaches with environment-specific reasons
- The exact commands that worked
- A clear environment section

## Running the standalone generator

```bash
# Interactive mode
python scripts/generate.py

# From JSON
python scripts/generate.py examples/github-push-input.json
```

The generated skill is saved to `~/.claude/skills/`.
