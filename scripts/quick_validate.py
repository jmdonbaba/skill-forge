#!/usr/bin/env python3
"""Validate a generated skill file for common issues.

Checks:
  - Frontmatter is valid YAML
  - Required fields and types; optional Skill Forge environment profile
  - No placeholder text remains
  - Heuristic trigger/command wording hints (not behavioral tests)
  - Environment section is complete
  - Description is sufficiently "pushy"

Usage:
  python scripts/quick_validate.py <path-to-skill.md>
  python scripts/quick_validate.py <path-to-skill.md> --strict
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path
from skill_common import ENV_KEYS, extract_frontmatter, validate_name


def extract_section(text: str, heading: str) -> str | None:
    """Extract a level-two section without treating fenced text as headings."""
    captured, active, fence = [], False, None
    for line in text.splitlines():
        if fence is None and re.match(r"^##[ \t]+", line):
            if active:
                break
            if re.match(rf"^##[ \t]+{re.escape(heading)}(?:[ \t]|$)", line):
                active = True
                continue
        if active:
            captured.append(line)
        fence = _next_fence(line, fence)
    return "\n".join(captured).strip() if active else None


def _next_fence(line, fence):
    match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
    if match:
        marker, suffix = match.groups()
        if fence is None:
            return marker
        if marker[0] == fence[0] and len(marker) >= len(fence) and not suffix.strip():
            return None
    return fence


def extract_triggers(skill_text: str) -> list[str]:
    """Extract trigger phrases from the 'When to use' section."""
    section = extract_section(skill_text, "When to use")
    if not section:
        return []
    triggers = re.findall(r"^-\s+(.+)$", section, re.MULTILINE)
    return triggers


def extract_code_blocks(skill_text: str) -> list[str]:
    """Extract content from all code blocks."""
    blocks, captured, fence = [], [], None
    for line in skill_text.splitlines():
        next_fence = _next_fence(line, fence)
        if fence is not None and next_fence is None:
            content = "\n".join(captured).strip()
            if content:
                blocks.append(content)
            captured = []
        elif fence is not None:
            captured.append(line)
        fence = next_fence
    return blocks


def _has_command(text):
    return any(line.strip() and not line.lstrip().startswith(("#", "//"))
               for block in extract_code_blocks(text) for line in block.splitlines())

def validate(skill_path: str, strict: bool = False) -> tuple[list[str], list[str], list[str]]:
    path = Path(skill_path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"Cannot read skill: {exc}"], [], []
    return validate_text(text, strict=strict, skill_path=str(path))


def validate_text(text: str, strict: bool = False, skill_path: str = "") -> tuple[list[str], list[str], list[str]]:
    """Structural/schema checks; never executes commands or predicts model routing."""
    errors, warnings, suggestions = [], [], []
    placeholders = re.findall(r"\{\{.*?\}\}", text, re.DOTALL)
    if placeholders:
        errors.append(f"Unresolved placeholder text: {', '.join(placeholders)}")
    try:
        frontmatter, _, body = extract_frontmatter(text)
    except (ValueError, RecursionError) as exc:
        return errors + [f"Malformed frontmatter: {exc}"], warnings, suggestions
    if frontmatter is None:
        return errors + ["Missing YAML frontmatter: first line must be --- with a closing delimiter"], warnings, suggestions
    for key in ("name", "description"):
        value = frontmatter.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Frontmatter '{key}' must be a non-empty string")
    name = frontmatter.get("name")
    try:
        validate_name(name)
    except ValueError as exc:
        errors.append(str(exc))
    desc = frontmatter.get("description")
    if isinstance(desc, str) and desc.strip():
        if len(desc) > 1024:
            errors.append("Description exceeds 1024 characters")
        _check_description(desc, errors, warnings, suggestions)
    env = frontmatter.get("environment")
    if "environment" not in frontmatter:
        warnings.append("Missing environment mapping (Skill Forge profile)")
    elif not isinstance(env, dict):
        errors.append("Frontmatter environment must be a mapping")
    else:
        for key in ENV_KEYS:
            if not isinstance(env.get(key), str) or not env[key].strip():
                errors.append(f"environment.{key} must be a non-empty string")
    compatibility = frontmatter.get("compatibility")
    if "compatibility" not in frontmatter:
        warnings.append("Missing compatibility string (Skill Forge profile)")
    elif not isinstance(compatibility, str) or not compatibility.strip():
        errors.append("compatibility must be a non-empty string")
    _check_body(body, skill_path, errors, warnings, suggestions, strict)
    if strict:
        if skill_path and Path(skill_path).name == "SKILL.md" and Path(skill_path).parent.name != name:
            errors.append("Skill directory name must match frontmatter name")
        verification = extract_section(body, "Verification")
        if not verification or not _has_command(verification) or not re.search(r"Expected output:\s*\S", verification):
            errors.append("Verification requires a concrete code block and non-empty 'Expected output:'")
        for section in ("Quick start", "Proven approach"):
            value = extract_section(body, section)
            if not value or not _has_command(value):
                errors.append(f"{section} requires at least one non-empty command block")
        if env is None or compatibility is None:
            errors.append("Strict Skill Forge profile requires environment and compatibility")
        if _unclosed_fence(body):
            errors.append("Unclosed Markdown code fence")
    return errors, warnings, suggestions


def _unclosed_fence(body):
    fence = None
    for line in body.splitlines():
        fence = _next_fence(line, fence)
    return fence is not None


def _check_description(desc: str, errors: list, warnings: list, suggestions: list):
    """Check description quality."""
    desc_lower = desc.lower()
    words = len(desc.split())

    if len(desc.strip()) < 24:
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
    if len(words) < 2 and len(trigger.strip()) < 6:
        warnings.append(
            f"Trigger #{idx} ('{trigger}') is very short. Generic one-word triggers "
            "cause over-firing. Make it a natural phrase: 'push this to GitHub' not 'push'."
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
        if not extract_section(body, section):
            warnings.append(f"Missing or empty recommended section: '## {section}'")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_path")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    skill_path, strict = args.skill_path, args.strict

    errors, warnings, suggestions = validate(skill_path, strict=strict)

    path = Path(skill_path).resolve()
    name = path.parent.name if path.name == "SKILL.md" else path.stem

    # Print results
    total_issues = len(errors) + len(warnings) + len(suggestions)
    if total_issues == 0:
        print(f"PASS {name}: no structural issues found.")
        sys.exit(0)

    print(f"\n{'=' * 60}")
    print(f"  Validation results for: {name}")
    print(f"  {len(errors)} error(s), {len(warnings)} warning(s), {len(suggestions)} suggestion(s)")
    print(f"{'=' * 60}\n")

    if errors:
        print("ERRORS (must fix):")
        for e in errors:
            print(f"  - {e}")
        print()

    if warnings:
        print("WARNINGS (should fix):")
        for w in warnings:
            wrapped = textwrap.fill(w, width=70, initial_indent="  - ", subsequent_indent="    ")
            print(wrapped)
        print()

    if suggestions:
        print("SUGGESTIONS:")
        for s in suggestions:
            wrapped = textwrap.fill(s, width=70, initial_indent="  - ", subsequent_indent="    ")
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
