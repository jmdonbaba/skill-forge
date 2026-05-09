# skill-forge: Generate a personalized skill from a completed task

You are helping the user turn a successfully-completed task into a reusable Claude Code skill. The user has finished something that took multiple tries, often due to environment-specific issues (network, OS, shell, missing tools).

## Process

### Step 1 — Gather the story

Ask questions to understand what happened. You need four categories of information:

**The task**
- What was the user trying to do? (one sentence)
- What phrases would the user naturally use to ask for this again? (these become skill triggers)

**The failures** (at least 2)
- What approach did the agent try first? Why did it fail?
- What was the second attempt? Why did that fail too?
- Be specific about the environment cause (e.g., "GFW blocks GitHub on port 443" not "network issue")

**The success**
- What exact steps finally worked?
- What was the key insight or workaround?
- List every command that actually ran successfully (copy-paste, don't paraphrase)

**The environment**
- OS and version (e.g., Windows 11 Home China 10.0.26100)
- Shell (e.g., Git Bash / mingw64, PowerShell 7, zsh)
- Network (e.g., GFW — requires proxy 127.0.0.1:7890 via Clash Verge)
- Relevant tools and versions

### Step 2 — Fill the template

Use `templates/skill-template.md` as the structure. Rules:

- Every command must be one the user **actually** ran successfully. No placeholders.
- Every pitfall must be one the user **actually** hit. No hypotheticals.
- The environment section must be complete — this is what makes the skill personalized.
- Trigger phrases should match how the user naturally talks about this task.
- Write in the user's language (Chinese or English, match their input).

### Step 3 — Save the skill

Save to `~/.claude/skills/{skill-name}.md`. The filename uses kebab-case.

Confirm to the user:
- Path where the skill was saved
- That it's available as `/{skill-name}` in future sessions
- They can manually edit it at any time
