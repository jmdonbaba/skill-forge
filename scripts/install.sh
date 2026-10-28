#!/usr/bin/env bash
# Install skill-forge as a Claude Code skill.
# Python does the same complete installation on Windows, macOS and Linux.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${PYTHON:-}" ]]; then
    exec "${PYTHON}" "${SCRIPT_DIR}/install.py" "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 "${SCRIPT_DIR}/install.py" "$@"
else
    exec python "${SCRIPT_DIR}/install.py" "$@"
fi
