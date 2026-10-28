#!/usr/bin/env python3
"""Generate a skill interactively or from JSON; validate before publishing."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from skill_common import SKILLS_DIR, save_skill, validate_name, yaml
from quick_validate import validate_text

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "skill-template.md"


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _text(value, label, required=True):
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f"{label} must be a {'non-empty ' if required else ''}string")
    return value


def _collection(data, array_key, pattern, fields=None):
    """Read either arrays or all legacy numbered entries, without truncation."""
    indexed = sorted({int(m.group(1)) for key in data if (m := re.fullmatch(pattern, key))})
    if array_key in data:
        if indexed:
            raise ValueError(f"Use either {array_key} or indexed fields, not both")
        values = data[array_key]
        if not isinstance(values, list):
            raise ValueError(f"{array_key} must be an array")
    elif fields:
        values = [{field: data.get(key.format(i=i), "") for field, key in fields.items()} for i in indexed]
    else:
        prefix = "TRIGGER" if array_key == "triggers" else "QUICK_START_COMMAND"
        values = [data[f"{prefix}_{i}"] for i in indexed]
    if fields:
        # Empty legacy slots are supported, but partial entries must not vanish.
        values = [value for value in values if value != {key: "" for key in fields}]
        for i, value in enumerate(values, 1):
            if not isinstance(value, dict) or set(value) != set(fields):
                raise ValueError(f"{array_key}[{i}] must contain {', '.join(fields)}")
            for field in fields:
                _text(value[field], f"{array_key}[{i}].{field}")
    else:
        values = [value for value in values if value != ""]
        for i, value in enumerate(values, 1):
            _text(value, f"{array_key}[{i}]")
    if not values:
        raise ValueError(f"{array_key} requires at least one entry")
    return values


def code_block(command):
    fence = '`' * max(3, max((len(m.group()) + 1 for m in re.finditer(r'`+', command)), default=3))
    return f"{fence}bash\n{command}\n{fence}"


def table_cell(value):
    return value.replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def fill_template(template: str, data: dict) -> str:
    if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
        raise ValueError("Input JSON must be an object with string keys")
    required = ("SKILL_NAME", "ONE_LINE_DESCRIPTION", "TRIGGER_CONTEXT_HINT", "ENVIRONMENT_HINT",
                "COMPATIBILITY", "OS", "SHELL", "NETWORK", "TOOLS", "ENVIRONMENT_WHY",
                "VERIFY_COMMAND", "EXPECTED_OUTPUT")
    values = {key: _text(data.get(key), key) for key in required}
    validate_name(values["SKILL_NAME"])
    for key in ("QUICK_START_NOTE", "ADDITIONAL_NOTES", "SEE_ALSO"):
        values[key] = _text(data.get(key, ""), key, required=False)
    triggers = _collection(data, "triggers", r"TRIGGER_(\d+)")
    quick_start = _collection(data, "quick_start", r"QUICK_START_COMMAND_(\d+)")
    steps = _collection(data, "steps", r"STEP_(\d+)_(?:TITLE|COMMAND|WHY)",
                        {"title": "STEP_{i}_TITLE", "command": "STEP_{i}_COMMAND", "why": "STEP_{i}_WHY"})
    pitfalls = _collection(data, "pitfalls", r"(?:BAD_APPROACH|WHY_FAILS|FAIL_SYMPTOM)_(\d+)",
                           {"approach": "BAD_APPROACH_{i}", "why": "WHY_FAILS_{i}", "symptom": "FAIL_SYMPTOM_{i}"})
    frontmatter = {
        "name": values["SKILL_NAME"],
        "description": f"{values['ONE_LINE_DESCRIPTION'].rstrip('.')}. Use when the user {values['TRIGGER_CONTEXT_HINT']}; especially {values['ENVIRONMENT_HINT']}.",
        "compatibility": values["COMPATIBILITY"],
        "environment": {key: values[key.upper()] for key in ("os", "shell", "network", "tools")},
    }
    values.update({
        "FRONTMATTER": yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip(),
        "GENERATED_AT": datetime.now(timezone.utc).isoformat(),
        "TRIGGERS": "\n".join(f"- {trigger}" for trigger in triggers),
        "QUICK_START": code_block("\n".join(quick_start)),
        "STEPS": "\n\n".join(f"### {i}. {step['title']}\n\n{code_block(step['command'])}\n\n{step['why']}" for i, step in enumerate(steps, 1)),
        "PITFALLS": "\n".join("| " + " | ".join(table_cell(p[field]) for field in ("approach", "why", "symptom")) + " |" for p in pitfalls),
        "VERIFICATION": code_block(values["VERIFY_COMMAND"]),
    })
    values.update({key + "_TABLE": table_cell(values[key]) for key in ("OS", "SHELL", "NETWORK", "TOOLS")})
    # A single pass avoids interpreting user content as another variable.
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: values.get(m.group(1), m.group()), template)


def collect_triggers() -> list[str]:
    triggers = []
    print("Enter trigger phrases; empty line to finish.")
    while value := input(f"  Trigger {len(triggers) + 1}: ").strip():
        triggers.append(value)
    return triggers


def collect_steps() -> list[dict]:
    steps = []
    print("Enter successful steps; empty title to finish.")
    while title := input(f"  Step {len(steps) + 1} title: ").strip():
        steps.append({"title": title, "command": input("  Command: "), "why": input("  Why: ")})
    return steps


def collect_pitfalls() -> list[dict]:
    pitfalls = []
    print("Enter observed failures; empty approach to finish.")
    while approach := input(f"  Failed approach {len(pitfalls) + 1}: ").strip():
        pitfalls.append({"approach": approach, "why": input("  Cause or hypothesis: "), "symptom": input("  Observed symptom: ")})
    return pitfalls


def collect_input() -> dict:
    prompts = {
        "SKILL_NAME": "Skill name (kebab-case)", "ONE_LINE_DESCRIPTION": "One-line description",
        "TRIGGER_CONTEXT_HINT": "When should this trigger? User…", "ENVIRONMENT_HINT": "Applicable environment",
        "COMPATIBILITY": "Required tools/versions", "OS": "OS and version", "SHELL": "Shell",
        "NETWORK": "Network/proxy constraints", "TOOLS": "Tools and versions", "ENVIRONMENT_WHY": "Why this environment matters",
    }
    data = {key: input(prompt + ": ").strip() for key, prompt in prompts.items()}
    data["triggers"] = collect_triggers()
    commands = []
    while command := input(f"  Quick start command {len(commands) + 1} (empty to finish): "):
        commands.append(command)
    data["quick_start"] = commands
    data["QUICK_START_NOTE"] = input("Quick start note (optional): ")
    data["steps"] = collect_steps()
    data["pitfalls"] = collect_pitfalls()
    for key, prompt in (("VERIFY_COMMAND", "Verification command"), ("EXPECTED_OUTPUT", "Expected output"),
                        ("ADDITIONAL_NOTES", "Additional notes (optional)"), ("SEE_ALSO", "See also (optional)")):
        data[key] = input(prompt + ": ")
    return data


def generate_skill(data, *, dry_run=False, validate=False, strict=False, skills_dir=SKILLS_DIR, force=False):
    content = fill_template(load_template(), data)
    errors, warnings, _ = validate_text(content, strict=strict)
    if errors or (strict and warnings):
        raise ValueError("Validation failed:\n" + "\n".join(errors + (warnings if strict else [])))
    if dry_run:
        print(content, end="")
        return None
    path = save_skill(content, Path(skills_dir), data["SKILL_NAME"], force=force)
    print(f"Skill saved to: {path}\nInvoke with: /{data['SKILL_NAME']}")
    if validate or strict:
        print("Structural validation passed; commands and trigger behavior were not executed.")
        for warning in warnings:
            print(f"Warning: {warning}")
    return path


def from_json(json_path: str, dry_run=False, validate=False, **kwargs):
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return generate_skill(data, dry_run=dry_run, validate=validate, **kwargs)


def interactive_generate(**kwargs):
    return generate_skill(collect_input(), **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON input; omit for interactive mode")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true", help="Report validation (structural errors always block saving)")
    parser.add_argument("--strict", action="store_true", help="Also check semantic completeness; warnings block saving")
    parser.add_argument("--force", action="store_true", help="Replace existing skill after backup")
    parser.add_argument("--skills-dir", type=Path, default=SKILLS_DIR)
    args = parser.parse_args()
    options = {key: value for key, value in vars(args).items() if key != "input"}
    try:
        if args.input:
            from_json(args.input, **options)
        else:
            interactive_generate(**options)
    except (OSError, ValueError, EOFError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
