#!/usr/bin/env bash
# Install skill-forge as a Claude Code skill.
# Run from the skill project root directory.

set -euo pipefail

SKILL_DIR="${HOME}/.claude/skills"
SKILL_FILE="skill-forge.md"

mkdir -p "${SKILL_DIR}"

# Copy the skill definition
cp "$(dirname "$0")/../SKILL.md" "${SKILL_DIR}/${SKILL_FILE}"

echo "✓ Installed skill-forge to ${SKILL_DIR}/${SKILL_FILE}"
echo "  Invoke with: /skill-forge"
echo ""
echo "Template files remain in this project directory."
echo "Generated skills will be saved to: ${SKILL_DIR}/"
