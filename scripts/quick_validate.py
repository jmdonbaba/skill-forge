#!/usr/bin/env python3
"""Validate a generated skill file for common issues.

Checks:
  - Frontmatter is valid YAML
  - Required fields present (name, description, environment)
  - No placeholder text remains
  - Trigger phrases are specific enough
  - Commands look concrete
  - Environment section is complete
  - Description is sufficiently "pushy"

Usage:
  python scripts/quick_validate.py <path-to-skill.md>
  python scripts/quick_validate.py <path-to-skill.md> --strict
"""

import re
import sys
import textwrap
from pathlib import Path


def extract_frontmatter(text: str) -> tuple[dict | None, str, str]:
    """Parse YAML frontmatter from skill text. Returns (data, frontmatter_raw, body)."""
    if not text.startswith("---"):
        return None, "", text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "", text

    return _parse_simple_yaml(parts[1]), parts[1], parts[2]


def _parse_simple_yaml(raw: str) -> dict:
    """Minimal YAML parser for frontmatter — avoids PyYAML dependency."""
    data = {}
    current_key = None
    current_value = ""
    indent = 0

    lines = raw.split("\n")
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        # Detect key: value lines
        match = re.match(r"^(\s*)([\w-]+)\s*:\s*(.*)?$", line)
        if match and not match.group(1) or (current_key and len(match.group(1)) <= indent):
            # Save previous key
            if current_key:
                data[current_key] = current_value.strip() if current_value.strip() else None
            current_key = match.group(2)
            current_value = match.group(3) or ""
            indent = 0
        elif current_key and line.startswith("  "):
            # Continuation of previous value (multi-line)
            if not indent:
                indent = len(line) - len(line.lstrip())
            continuation = line[indent:] if indent else line.strip()
            current_value = current_value + " " + continuation.strip()
        elif current_key:
            # Save previous key, start new
            data[current_key] = current_value.strip() if current_value.strip() else None
            current_key = None
            current_value = ""

    if current_key:
        data[current_key] = current_value.strip() if current_value.strip() else None

    return data


def extract_section(text: str, heading: str) -> str | None:
    """Extract content under a markdown heading."""
    pattern = rf"^##\s+{re.escape(heading)}.*?\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else None


def extract_triggers(skill_text: str) -> list[str]:
    """Extract trigger phrases from the 'When to use' section."""
    section = extract_section(skill_text, "When to use")
    if not section:
        return []
    triggers = re.findall(r"^-\s+(.+)$", section, re.MULTILINE)
    return triggers


def extract_code_blocks(skill_text: str) -> list[str]:
    """Extract content from all code blocks."""
    blocks = re.findall(r"```(?:bash|shell)?\s*\n(.*?)```", skill_text, re.DOTALL)
    return [b.strip() for b in blocks]


def validate(skill_path: str, strict: bool = False) -> tuple[list[str], list[str], list[str]]:
    """Validate a skill file. Returns (errors, warnings, suggestions)."""
    errors = []
    warnings = []
    suggestions = []

    path = Path(skill_path)
    if not path.exists():
        errors.append(f"File not found: {skill_path}")
        return errors, warnings, suggestions

    text = path.read_text(encoding="utf-8")
    frontmatter, fm_raw, body = extract_frontmatter(text)

    # === Frontmatter checks ===
    if frontmatter is None:
        errors.append("Missing or malformed YAML frontmatter (file must start with ---)")
        return errors, warnings, suggestions

    # Required fields
    required = ["name", "description"]
    for field in required:
        if field not in frontmatter or not frontmatter[field]:
            errors.append(f"Missing required frontmatter field: '{field}'")

    # Environment in frontmatter
    if "environment" not in frontmatter:
        warnings.append("Missing 'environment' key in frontmatter — environment context is what makes skills personalized")
    elif isinstance(frontmatter.get("environment"), dict):
        env = frontmatter["environment"]
        for key in ["os", "shell", "network", "tools"]:
            if key not in env or not env[key]:
                warnings.append(f"Missing environment.{key} — incomplete environment context")

    # Compatibility
    if "compatibility" not in frontmatter:
        warnings.append("Missing 'compatibility' field — list required tools/versions")

    # Description quality
    desc = frontmatter.get("description", "")
    if desc:
        _check_description(desc, errors, warnings, suggestions)
    else:
        errors.append("Description is empty — this is the primary trigger mechanism")

    # Name format
    name = frontmatter.get("name", "")
    if name and (" " in name or name != name.lower()):
        warnings.append(f"Skill name '{name}' should be kebab-case (lowercase, hyphens)")

    # === Body checks ===
    _check_body(body, skill_path, errors, warnings, suggestions, strict)

    return errors, warnings, suggestions


def _check_description(desc: str, errors: list, warnings: list, suggestions: list):
    """Check description quality."""
    desc_lower = desc.lower()
    words = len(desc.split())

    if words < 6:
        warnings.append(
            f"Description is very short ({words} words). A good description claims the "
            "contexts where this skill should trigger. Consider making it 'pushy' — "
            "e.g., 'Use whenever the user mentions X, Y, or Z, especially from Windows.'"
        )

    # Check for trigger-claiming language
    pushy_phrases = ["use when", "use whenever", "trigger", "invoke", "especially when"]
    if not any(phrase in desc_lower for phrase in pushy_phrases):
        suggestions.append(
            "Description may be too passive. Consider adding trigger-claiming language like "
            "'Use whenever the user mentions ...' or 'especially when ...' to improve triggering."
        )

    # Check for environment hint
    env_keywords = ["windows", "china", "proxy", "gfw", "macos", "linux", "git bash",
                    "powershell", "zsh", "bash", "network", "firewall", "corporate"]
    if not any(kw in desc_lower for kw in env_keywords):
        suggestions.append(
            "Description lacks environment context. Including OS/network hints helps "
            "the skill trigger when those conditions are present."
        )


def _check_body(body: str, skill_path: str, errors: list, warnings: list,
                suggestions: list, strict: bool):
    """Check the markdown body for issues."""

    # Placeholder detection
    placeholders = re.findall(r"\{\{.*?\}\}", body)
    # Filter out valid template variables (only used in template, not in generated skills)
    filtered = [p for p in placeholders if
                not any(p.startswith(f"{{{{{kw.upper()}}}}}") for kw in
                        ["SKILL_NAME", "ONE_LINE_DESCRIPTION", "OS", "SHELL", "NETWORK",
                         "TOOLS", "TRIGGER", "STEP", "BAD_APPROACH", "WHY_FAILS",
                         "VERIFY_COMMAND", "ADDITIONAL_NOTES", "COMPATIBILITY",
                         "ENVIRONMENT_WHY", "ENVIRONMENT_HINT", "TRIGGER_CONTEXT_HINT",
                         "QUICK_START", "EXPECTED_OUTPUT", "SEE_ALSO", "FAIL_SYMPTOM"])]
    if filtered:
        errors.append(f"Placeholder text found: {', '.join(filtered)}")

    # TODO/FIXME detection
    todos = re.findall(r"\b(TODO|FIXME|HACK|XXX)\b", body, re.IGNORECASE)
    if todos:
        errors.append(f"Unresolved markers found: {', '.join(set(todos))}")

    # Trigger phrase checks
    triggers = extract_triggers(body)
    if not triggers:
        warnings.append("No trigger phrases found in 'When to use' section")
    else:
        for i, trigger in enumerate(triggers):
            _check_trigger(trigger, i + 1, errors, warnings, suggestions)

    # Command checks
    code_blocks = extract_code_blocks(body)
    if not code_blocks:
        warnings.append("No code blocks found — skill may lack concrete commands")
    else:
        for block in code_blocks:
            _check_commands(block, errors, warnings, suggestions)

    # Section completeness
    _check_sections(body, errors, warnings)

    # Length check
    lines = body.count("\n")
    if lines < 20:
        warnings.append(f"Skill body is very short ({lines} lines) — may lack sufficient detail")
    if lines > 500:
        warnings.append(
            f"Skill body is long ({lines} lines). Consider splitting into "
            "references/ or scripts/ for progressive disclosure."
        )


def _check_trigger(trigger: str, idx: int, errors: list, warnings: list, suggestions: list):
    """Check a single trigger phrase."""
    words = trigger.split()
    if len(words) < 2:
        warnings.append(
            f"Trigger #{idx} ('{trigger}') is very short. Generic one-word triggers "
            "cause over-firing. Make it a natural phrase: 'push this to GitHub' not 'push'."
        )
    if '"' in trigger or "'" in trigger:
        warnings.append(
            f"Trigger #{idx} contains quotes — trigger phrases should be natural speech, "
            "not quoted strings. Remove the quotes."
        )


def _check_commands(block: str, errors: list, warnings: list, suggestions: list):
    """Check commands in a code block."""
    lines = block.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        # Check for abstract/placeholder commands
        if re.match(r"^(npm|pip|brew|apt|yum|dnf)\s+(install|add)\s+(package|pkg|module)$",
                     stripped, re.IGNORECASE):
            warnings.append(
                f"Command looks abstract: '{stripped}' — use the actual package name, "
                "not a placeholder."
            )

        # Check for "your-X" placeholders
        if re.search(r"\b(your-\w+|my-\w+|some-\w+)\b", stripped, re.IGNORECASE):
            warnings.append(
                f"Command contains placeholder: '{stripped}' — replace 'your-*' with "
                "the actual value used."
            )

    # Check for multi-line commands without && or line continuation
    if len(lines) > 5:
        suggestions.append(
            f"Code block has {len(lines)} lines. Consider using && for multi-step "
            "commands or splitting into separate blocks with explanatory text."
        )


def _check_sections(body: str, errors: list, warnings: list):
    """Check required sections exist."""
    required_sections = ["Environment", "When to use", "Proven approach", "Pitfalls"]
    for section in required_sections:
        if not re.search(rf"^##\s+{section}", body, re.MULTILINE):
            # Pitfalls might also be titled "Pitfalls — what NOT to do"
            alt_pattern = rf"^##\s+{re.escape(section)}\b"
            if not re.search(alt_pattern, body, re.MULTILINE):
                warnings.append(f"Missing recommended section: '## {section}'")


def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_validate.py <path-to-skill.md> [--strict]")
        sys.exit(1)

    skill_path = sys.argv[1]
    strict = "--strict" in sys.argv

    errors, warnings, suggestions = validate(skill_path, strict=strict)

    name = Path(skill_path).stem

    # Print results
    total_issues = len(errors) + len(warnings) + len(suggestions)
    if total_issues == 0:
        print(f"✓ {name}: Passed — no issues found.")
        sys.exit(0)

    print(f"\n{'=' * 60}")
    print(f"  Validation results for: {name}")
    print(f"  {len(errors)} error(s), {len(warnings)} warning(s), {len(suggestions)} suggestion(s)")
    print(f"{'=' * 60}\n")

    if errors:
        print("❌ ERRORS (must fix):")
        for e in errors:
            print(f"  • {e}")
        print()

    if warnings:
        print("⚠️  WARNINGS (should fix):")
        for w in warnings:
            wrapped = textwrap.fill(w, width=70, initial_indent="  • ", subsequent_indent="    ")
            print(wrapped)
        print()

    if suggestions:
        print("💡 SUGGESTIONS:")
        for s in suggestions:
            wrapped = textwrap.fill(s, width=70, initial_indent="  • ", subsequent_indent="    ")
            print(wrapped)
        print()

    if errors:
        sys.exit(1)
    elif strict and warnings:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
