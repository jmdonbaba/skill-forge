---
name: skill-forge
description: >-
  Distill a winding, trial-and-error task into a reusable Claude Code skill.
  Use after any task where the agent hit dead ends before finding the winning
  path — especially when dead ends were caused by environment-specific issues
  (OS, shell, network, proxy). Capture what failed AND what worked so future
  sessions skip the detours.
---

# skill-forge: Forge hard-won knowledge into reusable skills

You help the user turn a successfully-completed task into a reusable Claude Code skill. The task was hard-won — multiple approaches failed before one worked, usually because the user's environment (OS, shell, network) isn't what agents expect by default.

**Your job**: extract what happened, generate a skill that prevents repeating the same dead ends, validate it, and tune the description so it triggers reliably.

## Process

### Step 1 — Gather the story

Ask questions to understand what happened. The user just finished something that took multiple tries. Your goal is to extract the *environment-specific* details that made this hard.

Four categories you need:

**The task**
- What was the user trying to do? One concrete sentence.
- Imagine the user comes back in 2 weeks and asks for this again — what would they say? Write down 3-5 natural phrases. These become trigger phrases.

**The failures** — this is the most valuable part of the skill
- What approach was tried first? Why did it fail?
- What was the second attempt? Why did that fail too?
- Get at least 2 dead ends. Be painfully specific about the environment cause.
  - "GFW blocks GitHub on port 443" not "network issue"
  - "Git Bash doesn't expand `~` in nested double quotes" not "path problem"
- Every recorded pitfall saves a future session from the same dead end

**The success**
- What exact steps finally worked, in order?
- What was the key insight or workaround?
- List every command that actually ran successfully. Copy-paste from the conversation — do NOT paraphrase or guess. One wrong flag wastes more time than no skill at all.

**The environment**
- OS and version (e.g., Windows 11 Home China 10.0.26100)
- Shell (e.g., Git Bash / mingw64, PowerShell 7, zsh 5.9)
- Network constraints (e.g., GFW — proxy at 127.0.0.1:7890 via Clash Verge)
- Relevant tools and versions (e.g., git 2.47.0, node 22.11.0)

### Step 2 — Confirm before generating

Before writing anything, present a summary to the user:

- The task (one line)
- The winning approach (2-3 steps)
- The pitfalls (2+ dead ends)
- The environment block

Ask: "Does this look right? Anything I missed?"

This confirmation step prevents generating a skill that's wrong — which is worse than no skill, because wrong skills lead every future session astray.

### Step 3 — Fill the template

Use `templates/skill-template.md`. Iron rules:

1. **Every command must be one the user actually ran.** No placeholders. No "something like this." If you're not sure, ask.
2. **Every pitfall must be one the user actually hit.** No "here's what might go wrong." Only real scars.
3. **The environment section must be complete.** This is what makes the skill personal. A skill without environment context is a recipe without a kitchen.
4. **Trigger phrases should match how the user naturally talks.** Use their actual phrasing from the conversation.
5. **Write in the user's language.** Match their input — Chinese or English. Don't translate.

### Step 4 — Validate

After writing the skill, run the quick validator:

```bash
python scripts/quick_validate.py ~/.claude/skills/{skill-name}.md
```

The validator checks:
- Frontmatter is valid YAML
- Required fields are present (name, description, environment)
- No placeholder text remains (no `{{...}}`, `TODO`, `FIXME`)
- Trigger phrases are specific enough (not single generic words)
- Commands look concrete (contain flags, arguments, or specific syntax)
- Environment section has all four keys (os, shell, network, tools)

If validation fails, fix the issues and re-run. Don't skip this step — it catches the most common mistakes.

### Step 5 — Tune the description

The `description` in the frontmatter is the primary mechanism that determines whether Claude invokes the skill. A bad description means the skill sits dormant while the agent repeats the same dead ends.

What makes a good description:

- **Be "pushy."** Don't just describe — claim the contexts where it should fire. Instead of "How to push to GitHub", write "Push a local project to GitHub. Use whenever the user mentions pushing, uploading, or putting code on GitHub — especially from Windows or behind a network proxy."
- **Include the environment hook.** Mention the OS/shell/network constraints in the description. It grabs attention when those conditions are present.
- **Be specific.** "Help with git operations" triggers for every git question and is useless. "Push to GitHub from Windows behind GFW/proxy" triggers only when it should.
- **Include both formal and casual phrasing.** Users say "put this on GitHub" not "push to a remote repository." Cover how real people talk.

Review the description with the user. Offer alternative phrasings. A badly-triggering skill is noise; a well-triggered one is invisible infrastructure.

### Step 6 — Save and confirm

Save to `~/.claude/skills/{skill-name}.md`. The filename uses kebab-case.

Tell the user:
- Path where the skill was saved
- That it's available as `/{skill-name}` in future sessions
- They can manually edit it anytime at that path
- Suggest they test it: type one of the trigger phrases in a new session

## What makes a good skill

**Worth forging:**
- Proxy configs, mirror URLs, PATH quirks — environment workarounds
- Platform differences (Windows vs macOS vs Linux)
- Shell-specific syntax (Git Bash vs PowerShell vs zsh)
- Toolchain bugs or version-specific behavior
- Permission, firewall, admin-rights issues

**Not worth forging:**
- One-off tasks you'll never do again
- Generic solutions already documented in official docs
- Tasks that worked on the first try with no dead ends

## When NOT to use skill-forge

- The task worked first try with no environment issues → nothing to capture
- The user wants to design a skill from scratch → use `/skill-creator` instead
- The user is iteratively improving an existing skill through evals → use `/skill-creator` instead

skill-forge is specifically for **post-task capture** — extracting a winning path from real trial-and-error. For designing new skills or running eval-driven iterations, skill-creator is the right tool.
