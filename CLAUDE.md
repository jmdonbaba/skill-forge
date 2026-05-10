# skill-forge project

Distill winding agent task completions into reusable, environment-aware Claude Code skills.

## What this project does

- Defines a meta-skill (`SKILL.md`) that teaches Claude Code how to generate new skills from completed task experiences
- Provides a Python script (`scripts/generate.py`) for standalone skill generation (interactive or JSON-driven)
- Includes a quick validator (`scripts/quick_validate.py`) that checks generated skills for common issues
- Captures environment-specific context (OS, shell, proxy, tool versions) in each generated skill
- Records pitfalls (failed approaches) alongside the winning path — so future sessions skip the dead ends

## Project context

Claude Code skills live in `~/.claude/skills/`. Each skill is a `.md` file with YAML frontmatter. The meta-skill defined here (`SKILL.md`) gets installed there via `scripts/install.sh`.

When a user invokes `/skill-forge`, Claude:
1. Gathers the story — task, failures, success, and environment
2. Confirms the summary with the user before generating
3. Generates a skill file using the template at `templates/skill-template.md`
4. Runs `quick_validate.py` to catch common issues (placeholders, missing fields, weak triggers)
5. Tunes the description for reliable triggering
6. Saves the generated skill to `~/.claude/skills/{name}.md`

## Key design decisions

- **Environment-first**: Every skill records OS, shell, network constraints. Generic skills are useless in edge-case environments.
- **Pitfalls before solutions**: Recording what *didn't* work is more valuable than what did — it prevents repeating the same dead ends.
- **Verified commands only**: Never generate placeholder commands. Every command in a skill must be one that actually ran successfully.
- **Pushy descriptions**: The frontmatter `description` field should actively claim triggering contexts (e.g., "Use whenever the user mentions X, Y, or Z, especially from Windows"). Passive descriptions cause undertriggering.
- **Confirm before saving**: Present a summary to the user before writing the skill — a wrong skill is worse than no skill.
- **Keep skills focused**: One skill = one task domain. Resist the urge to make a "general tips" skill.

## Comparison with skill-creator

This project complements Anthropic's official `skill-creator` (193K+ installs). Key differences:

| | skill-forge | skill-creator |
|---|---|---|
| Entry point | Post-task: "I just finished something that took 5 tries" | Pre-task: "I want to design a skill for X" |
| Process | Extract from conversation → one-shot generation | Draft → eval → iterate → improve |
| Focus | Environment-specific pitfalls | General-purpose skill design |
| Evaluation | User confirmation + quick_validate.py | Parallel subagent runs, blind A/B, quantitative benchmarks |

Use skill-forge when you've just completed a winding task and want to capture the winning path. Use skill-creator when you're designing a skill from scratch or running eval-driven iterations.

## Adding examples

Place new examples in `examples/`. Each example is a complete skill file showing what the finished output looks like. Name them descriptively (e.g., `docker-push-china.md`, `npm-install-proxy.md`).

Good examples include:
- 2+ failed approaches with environment-specific reasons
- The exact commands that worked
- A complete environment section
- Natural trigger phrases in the user's actual language

## Running the tools

```bash
# Interactive skill generation
python scripts/generate.py

# From JSON
python scripts/generate.py examples/github-push-input.json

# Dry-run (print to stdout, don't save)
python scripts/generate.py examples/github-push-input.json --dry-run

# Generate + validate
python scripts/generate.py examples/github-push-input.json --validate

# Validate an existing skill
python scripts/quick_validate.py ~/.claude/skills/github-push.md
python scripts/quick_validate.py ~/.claude/skills/github-push.md --strict
```

The generated skill is saved to `~/.claude/skills/`.
