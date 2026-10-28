"""Shared naming, frontmatter parsing and safe storage for Skill Forge."""

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import tempfile
from uuid import uuid4

try:
    import yaml
except ImportError as exc:
    raise SystemExit("Missing PyYAML. Run: python -m pip install -r requirements.txt") from exc

SKILLS_DIR = Path.home() / ".claude" / "skills"
ENV_KEYS = ("os", "shell", "network", "tools")


def validate_name(name: str) -> str:
    """Use portable kebab-case names; never accept a path as a skill name."""
    reserved = {"con", "prn", "aux", "nul", "synced", "anthropic-skills"}
    reserved.update(f"{prefix}{i}" for prefix in ("com", "lpt") for i in range(1, 10))
    if (not isinstance(name, str) or len(name) > 64
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
            or name in reserved):
        raise ValueError("Skill name must be 1-64 lowercase letters/digits in kebab-case, and not a reserved name")
    return name


class UniqueKeyLoader(yaml.SafeLoader):
    """Do not silently discard earlier values when YAML keys are duplicated."""


def _mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            if key in result:
                raise ValueError(f"Duplicate YAML key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        except TypeError as exc:
            raise ValueError("YAML mapping keys must be scalar values") from exc
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def extract_frontmatter(text: str) -> tuple[dict | None, str, str]:
    """Parse only whole-line delimiters, with safe, real YAML parsing."""
    match = re.match(r"\A---\r?\n(.*?)^---[ \t]*(?:\r?\n|\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        return None, "", text
    try:
        data = yaml.load(match.group(1), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    return data, match.group(1), text[match.end():]


def skill_path(skills_dir: Path, name: str) -> Path:
    root = Path(skills_dir).expanduser().resolve()
    path = root / validate_name(name) / "SKILL.md"
    if path.parent.is_symlink() or path.is_symlink() or path.resolve().parent != path.parent:
        raise ValueError(f"Refusing redirected skill path: {path}")
    return path


def backup_path(root: Path, name: str) -> Path:
    """Keep backups outside the skills discovery directory."""
    directory = root.resolve().parent / "skill-forge-backups"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return directory / f"{name}-{stamp}-{uuid4().hex[:8]}.bak"


def save_skill(content: str, skills_dir: Path, name: str, force: bool = False) -> Path:
    path = skill_path(skills_dir, name)
    legacy = path.parent.parent / f"{name}.md"
    if legacy.is_symlink():
        raise ValueError(f"Refusing legacy symlink: {legacy}")
    existing = [p for p in (path, legacy) if p.exists()]
    if existing and not force:
        raise FileExistsError(f"Skill already exists: {existing[0]}. Use --force to replace with a backup.")
    for old in existing:
        backup = backup_path(path.parent.parent, name)
        shutil.copy2(old, backup)
        print(f"Backup saved to: {backup}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".SKILL-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(temporary, path)
        else:
            # Atomic no-clobber publication: fail if another writer won.
            os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path
