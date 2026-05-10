#!/usr/bin/env python3
"""Generate a personalized Claude Code skill from a JSON file or interactive input.

Usage:
  python scripts/generate.py                    # Interactive mode
  python scripts/generate.py input.json         # From JSON file
  python scripts/generate.py input.json --dry-run   # Print to stdout, don't save
  python scripts/generate.py input.json --validate  # Run validation after generation
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "skill-template.md"
SKILLS_DIR = Path.home() / ".claude" / "skills"


def load_template() -> str:
    """Load the skill template."""
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def get_skill_dir() -> Path:
    """Ensure the skills directory exists and return it."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    return SKILLS_DIR


def fill_template(template: str, data: dict) -> str:
    """Fill template placeholders with values.

    Handles {{VARIABLE}} placeholders. List values are joined with commas.
    Multi-line values are preserved.
    """
    result = template
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        if placeholder not in result:
            # Try uppercase conversion
            upper_placeholder = f"{{{{{key.upper()}}}}}"
            if upper_placeholder in result:
                placeholder = upper_placeholder
        if isinstance(value, list):
            value = "\n- ".join(value)
        result = result.replace(placeholder, str(value))
    return result


def collect_triggers() -> list[str]:
    """Collect trigger phrases interactively."""
    triggers = []
    print("Enter trigger phrases (natural ways the user would ask for this).")
    print("Press Enter on an empty line when done.\n")
    i = 1
    while True:
        t = input(f"  Trigger {i}: ").strip()
        if not t:
            break
        triggers.append(t)
        i += 1
        if i > 8:  # sanity cap
            break
    return triggers


def collect_steps() -> list[dict]:
    """Collect proven approach steps interactively."""
    steps = []
    print("Enter the steps that actually worked (in order).")
    print("Press Enter on an empty title when done.\n")
    i = 1
    while True:
        print(f"--- Step {i} ---")
        title = input("  Title: ").strip()
        if not title:
            break
        command = input("  Command: ").strip()
        why = input("  Why this is needed: ").strip()
        steps.append({"title": title, "command": command, "why": why})
        i += 1
        if i > 10:
            break
    return steps


def collect_pitfalls() -> list[dict]:
    """Collect pitfalls interactively."""
    pitfalls = []
    print("Enter failed approaches (what was tried and failed).")
    print("Press Enter on an empty approach when done.\n")
    i = 1
    while True:
        print(f"--- Pitfall {i} ---")
        approach = input("  Failed approach: ").strip()
        if not approach:
            break
        why = input("  Environment cause (why it failed): ").strip()
        symptom = input("  What happened (symptom): ").strip()
        pitfalls.append({"approach": approach, "why": why, "symptom": symptom})
        i += 1
        if i > 8:
            break
    return pitfalls


def interactive_generate():
    """Interactive Q&A to build a skill."""
    print()
    print("=" * 60)
    print("  skill-forge")
    print("  Forge your hard-won knowledge into a reusable skill")
    print("=" * 60)
    print()

    data = {}

    # Basic info
    print("── Basic info ──")
    data["SKILL_NAME"] = input("Skill name (kebab-case, e.g. github-push): ").strip()
    data["ONE_LINE_DESCRIPTION"] = input("One-line description: ").strip()
    data["TRIGGER_CONTEXT_HINT"] = input(
        "Trigger context hint (e.g., 'mentions pushing, uploading, or putting code on GitHub'): "
    ).strip()
    data["ENVIRONMENT_HINT"] = input(
        "Environment hint (e.g., 'from Windows', 'behind a corporate proxy'): "
    ).strip()
    data["COMPATIBILITY"] = input("Required tools/versions (e.g., 'git >=2.40, ssh'): ").strip()

    # Environment
    print("\n── Environment ──")
    data["OS"] = input("OS and version (e.g. Windows 11 Home China 10.0.26100): ").strip()
    data["SHELL"] = input("Shell (e.g. Git Bash / mingw64, PowerShell 7, zsh 5.9): ").strip()
    data["NETWORK"] = input("Network constraints (e.g. GFW, corporate proxy, none): ").strip()
    data["TOOLS"] = input("Key tools used: ").strip()
    data["ENVIRONMENT_WHY"] = input(
        "Why the environment matters (one sentence): "
    ).strip()

    # Triggers
    print("\n── Trigger phrases ──")
    triggers = collect_triggers()
    for i in range(5):
        data[f"TRIGGER_{i + 1}"] = triggers[i] if i < len(triggers) else ""

    # Quick start
    print("\n── Quick start (the minimal path) ──")
    qs_commands = []
    print("Enter the 1-3 most critical commands. Empty line when done.")
    i = 1
    while i <= 3:
        cmd = input(f"  Command {i}: ").strip()
        if not cmd:
            break
        qs_commands.append(cmd)
        i += 1
    for j in range(3):
        data[f"QUICK_START_COMMAND_{j + 1}"] = qs_commands[j] if j < len(qs_commands) else ""
    data["QUICK_START_NOTE"] = input("Quick start note (optional): ").strip()

    # Proven approach
    print("\n── Proven approach ──")
    steps = collect_steps()
    for i in range(3):
        if i < len(steps):
            data[f"STEP_{i + 1}_TITLE"] = steps[i]["title"]
            data[f"STEP_{i + 1}_COMMAND"] = steps[i]["command"]
            data[f"STEP_{i + 1}_WHY"] = steps[i]["why"]
        else:
            data[f"STEP_{i + 1}_TITLE"] = ""
            data[f"STEP_{i + 1}_COMMAND"] = ""
            data[f"STEP_{i + 1}_WHY"] = ""

    # Pitfalls
    print("\n── Pitfalls ──")
    pitfalls = collect_pitfalls()
    for i in range(3):
        if i < len(pitfalls):
            data[f"BAD_APPROACH_{i + 1}"] = pitfalls[i]["approach"]
            data[f"WHY_FAILS_{i + 1}"] = pitfalls[i]["why"]
            data[f"FAIL_SYMPTOM_{i + 1}"] = pitfalls[i]["symptom"]
        else:
            data[f"BAD_APPROACH_{i + 1}"] = ""
            data[f"WHY_FAILS_{i + 1}"] = ""
            data[f"FAIL_SYMPTOM_{i + 1}"] = ""

    # Verification
    print("\n── Verification ──")
    data["VERIFY_COMMAND"] = input("Verification command: ").strip()
    data["EXPECTED_OUTPUT"] = input("Expected output (one line): ").strip()

    # Notes
    data["ADDITIONAL_NOTES"] = input("Additional notes (optional): ").strip()
    data["SEE_ALSO"] = input("See also (links or related skills, optional): ").strip()

    # Generate
    print("\n" + "=" * 60)
    print("  Generating skill...")
    print("=" * 60)

    template = load_template()
    content = fill_template(template, data)

    # Header comment
    header = (
        f"<!-- Generated by skill-forge on {datetime.now().isoformat()} -->\n"
        f"<!-- Environment: {data['OS']} | {data['SHELL']} | {data['NETWORK']} -->\n\n"
    )

    skill_path = get_skill_dir() / f"{data['SKILL_NAME']}.md"
    skill_path.write_text(header + content, encoding="utf-8")

    print(f"\n  Skill saved to: {skill_path}")
    print(f"  Invoke with:     /{data['SKILL_NAME']}")
    print(f"  Edit at:         {skill_path}")
    print()


def from_json(json_path: str, dry_run: bool = False, validate: bool = False):
    """Generate skill from a JSON input file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    template = load_template()
    content = fill_template(template, data)

    header = (
        f"<!-- Generated by skill-forge on {datetime.now().isoformat()} -->\n"
        f"<!-- Environment: {data.get('OS', '?')} | "
        f"{data.get('SHELL', '?')} | {data.get('NETWORK', '?')} -->\n\n"
    )

    full_content = header + content
    skill_name = data.get("SKILL_NAME", "unknown")

    if dry_run:
        print(full_content)
        return

    skill_path = get_skill_dir() / f"{skill_name}.md"
    skill_path.write_text(full_content, encoding="utf-8")

    print(f"  Skill saved to: {skill_path}")
    print(f"  Invoke with:     /{skill_name}")

    if validate:
        print(f"\n  Validating...")
        _run_validation(skill_path)


def _run_validation(skill_path: Path) -> None:
    """Run quick_validate.py on the generated skill."""
    validator = Path(__file__).parent / "quick_validate.py"
    if not validator.exists():
        print(f"  Warning: validator not found at {validator}")
        return

    try:
        result = subprocess.run(
            [sys.executable, str(validator), str(skill_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"  Validation found issues — review and fix before using.")
    except FileNotFoundError:
        print(f"  Warning: Python not available, skipping validation.")
    except subprocess.TimeoutExpired:
        print(f"  Warning: Validation timed out, check manually.")


def print_usage():
    print(__doc__)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    do_validate = "--validate" in sys.argv

    # Filter out flags to find the positional argument
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(args) > 0:
        from_json(args[0], dry_run=dry_run, validate=do_validate)
    else:
        if dry_run:
            print("Error: --dry-run requires a JSON input file.")
            sys.exit(1)
        interactive_generate()
