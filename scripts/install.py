#!/usr/bin/env python3
"""Install the complete Skill Forge bundle from any working directory."""

import argparse
import os
from pathlib import Path
import shutil
import tempfile

from skill_common import SKILLS_DIR, backup_path, skill_path
from quick_validate import validate_text

SOURCE = Path(__file__).resolve().parent.parent


def install(skills_dir=SKILLS_DIR, force=False):
    target = skill_path(Path(skills_dir), "skill-forge").parent
    root = target.parent
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".skill-forge-install.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise FileExistsError(f"Installation lock exists: {lock}. Wait for the other installer; after a crash, remove only the stale lock and retry.") from exc
    try:
        os.close(fd)
        return _install_locked(target, force)
    finally:
        lock.unlink()


def _install_locked(target, force):
    root = target.parent
    legacy = root / "skill-forge.md"
    if legacy.is_symlink():
        raise ValueError(f"Refusing legacy symlink: {legacy}")
    if (target.exists() or legacy.exists()) and not force:
        raise FileExistsError(f"Skill Forge already exists under {root}. Use --force to replace with a full backup.")
    content = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
    errors, _, _ = validate_text(content)
    if errors:
        raise ValueError("Invalid bundled SKILL.md: " + "; ".join(errors))
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".skill-forge-stage-", dir=root) as temporary:
        staging = Path(temporary) / "skill-forge"
        staging.mkdir()
        for name in ("SKILL.md", "requirements.txt"):
            shutil.copy2(SOURCE / name, staging / name)
        for name in ("scripts", "templates"):
            shutil.copytree(SOURCE / name, staging / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # Another installation may have completed while the bundle was copied.
        skill_path(root, "skill-forge")
        if legacy.is_symlink():
            raise ValueError(f"Refusing legacy symlink: {legacy}")
        if (target.exists() or legacy.exists()) and not force:
            raise FileExistsError("Skill Forge appeared during installation; refusing replacement without --force")
        backup = None
        if legacy.exists():
            legacy_backup = backup_path(root, "skill-forge-legacy")
            shutil.copy2(legacy, legacy_backup)
            print(f"Legacy backup saved to: {legacy_backup}; original left in place")
        if target.exists():
            if not force:
                raise FileExistsError("Skill Forge appeared during installation; refusing replacement without --force")
            backup = backup_path(root, "skill-forge")
            os.rename(target, backup)
            print(f"Bundle backup saved to: {backup}")
        try:
            os.rename(staging, target)
        except OSError:
            if backup is not None and not target.exists():
                os.rename(backup, target)
            raise
    print(f"Installed Skill Forge to: {target / 'SKILL.md'}\nInvoke with: /skill-forge")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, default=SKILLS_DIR)
    parser.add_argument("--force", action="store_true", help="Replace existing bundle after backup")
    args = parser.parse_args()
    try:
        install(args.skills_dir, args.force)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
