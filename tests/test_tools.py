import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate
import quick_validate
import install
import skill_common


def bash_path():
    if os.name == "nt":
        path = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        return str(path) if path.is_file() else None
    return shutil.which("bash")


def sample():
    return json.loads((ROOT / "examples/github-push-input.json").read_text(encoding="utf-8"))


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"
        self.input = self.base / "input.json"

    def run_generator(self, data=None, *flags):
        self.input.write_text(json.dumps(sample() if data is None else data), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/generate.py"), str(self.input),
             "--skills-dir", str(self.skills), *flags],
            cwd=self.base, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "HOME": str(self.base), "USERPROFILE": str(self.base), "PYTHONUTF8": "1"},
            timeout=30,
        )

    def test_generated_skill_is_discoverable_and_valid(self):
        result = self.run_generator(None, "--validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        path = self.skills / "github-push/SKILL.md"
        self.assertTrue(path.is_file(), result.stdout)
        self.assertTrue(path.read_text(encoding="utf-8").startswith("---\n"))
        self.assertEqual(quick_validate.validate(str(path))[0], [])

    def test_dry_run_has_frontmatter_and_creates_nothing(self):
        result = self.run_generator(None, "--dry-run", "--validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("---\n"))
        self.assertFalse(self.skills.exists())

    def test_preserves_all_indexed_collections(self):
        data = sample()
        for i in range(1, 13):
            data[f"TRIGGER_{i}"] = f"unique trigger {i}"
            for suffix in ("TITLE", "COMMAND", "WHY"):
                data[f"STEP_{i}_{suffix}"] = f"unique step {i} {suffix}"
            for key in ("BAD_APPROACH", "WHY_FAILS", "FAIL_SYMPTOM"):
                data[f"{key}_{i}"] = f"unique pitfall {i} {key}"
        result = self.run_generator(data, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        for i in range(1, 13):
            for value in (f"unique trigger {i}", f"unique step {i} COMMAND", f"unique pitfall {i} BAD_APPROACH"):
                self.assertIn(value, result.stdout)

    def test_array_collections_preserved(self):
        data = sample()
        for key in list(data):
            if re.fullmatch(r"TRIGGER_\d+|STEP_\d+_\w+|(?:BAD_APPROACH|WHY_FAILS|FAIL_SYMPTOM)_\d+", key):
                del data[key]
        data["triggers"] = ["把这个项目推到 GitHub", "上传代码到远程仓库"]
        data["steps"] = [{"title": "Check branch", "command": "git branch --show-current", "why": "Read actual branch"}]
        data["pitfalls"] = [{"approach": "Assume main", "why": "Branch differs", "symptom": "Missing ref"}]
        result = self.run_generator(data, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(data["triggers"][0], result.stdout)
        self.assertIn("git branch --show-current", result.stdout)

    def test_names_cannot_escape_output_or_use_reserved_windows_names(self):
        for name in ("../escape", "a/b", "a\\b", "C:evil", "Bad Name", "con", "nul", "synced", "anthropic-skills", "a" * 65):
            with self.subTest(name=name):
                data = sample()
                data["SKILL_NAME"] = name
                result = self.run_generator(data)
                self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.skills.exists())

    def test_rejects_invalid_input_without_writing(self):
        for change in ({"OS": ""}, {"ONE_LINE_DESCRIPTION": []}, {"TRIGGER_1": "{{TRIGGER_1}}"}, {"VERIFY_COMMAND": None}):
            with self.subTest(change=change):
                data = sample()
                data.update(change)
                result = self.run_generator(data, "--validate")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.skills.exists())

    def test_yaml_special_characters_round_trip(self):
        data = sample()
        data["OS"] = "Windows: workstation #1"
        data["NETWORK"] = "on"
        data["ONE_LINE_DESCRIPTION"] = "Push: safely # keep detail\nwith Unicode 中文"
        result = self.run_generator(data, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        fm, _, _ = quick_validate.extract_frontmatter(result.stdout)
        self.assertEqual(fm["environment"]["os"], data["OS"])
        self.assertEqual(fm["environment"]["network"], "on")

    def test_overwrite_refused_then_force_backs_up(self):
        first = self.run_generator()
        self.assertEqual(first.returncode, 0, first.stderr)
        path = self.skills / "github-push/SKILL.md"
        original = path.read_bytes()
        data = sample()
        data["ADDITIONAL_NOTES"] = "Replacement version"
        again = self.run_generator(data)
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual(path.read_bytes(), original)
        forced = self.run_generator(data, "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertIn("Replacement version", path.read_text(encoding="utf-8"))
        self.assertTrue(any(p.is_file() and p.read_bytes() == original for p in self.base.rglob("*.bak")))

    def test_legacy_skill_is_not_silently_shadowed(self):
        self.skills.mkdir()
        legacy = self.skills / "github-push.md"
        legacy.write_text("previous improved skill", encoding="utf-8")
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(legacy.read_text(), "previous improved skill")

    def test_interactive_collection_keeps_every_item(self):
        # Exercise collection independently of terminal/UI; rendering is shared with JSON.
        with patch("builtins.input", side_effect=[f"trigger {i}" for i in range(8)] + [""]):
            self.assertEqual(len(generate.collect_triggers()), 8)

    def test_interactive_path_keeps_all_steps_and_pitfalls(self):
        data = sample()
        basics = [data[key] for key in ("SKILL_NAME", "ONE_LINE_DESCRIPTION", "TRIGGER_CONTEXT_HINT",
                  "ENVIRONMENT_HINT", "COMPATIBILITY", "OS", "SHELL", "NETWORK", "TOOLS", "ENVIRONMENT_WHY")]
        replies = basics + [f"trigger phrase {i}" for i in range(9)] + ["", "git status", "", ""]
        replies += [value for i in range(11) for value in (f"step {i}", f"echo step-{i}", "Observed success")]
        replies += [""] + [value for i in range(9) for value in (f"failure {i}", "Unconfirmed cause", "Observed failure")]
        replies += ["", "git status", "clean working tree", "", ""]
        with patch("builtins.input", side_effect=replies):
            path = generate.interactive_generate(skills_dir=self.skills, validate=True)
        text = path.read_text(encoding="utf-8")
        for value in ("trigger phrase 8", "echo step-10", "failure 8"):
            self.assertIn(value, text)

    def test_unknown_flags_fail_without_writing(self):
        self.assertNotEqual(self.run_generator(None, "--typo").returncode, 0)
        self.assertFalse(self.skills.exists())

    def test_strict_failure_never_overwrites_existing_skill(self):
        self.assertEqual(self.run_generator().returncode, 0)
        path = self.skills / "github-push/SKILL.md"
        original = path.read_bytes()
        data = sample()
        data["TRIGGER_1"] = "push"
        result = self.run_generator(data, "--strict", "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), original)


class InstallerTests(unittest.TestCase):
    @unittest.skipUnless(bash_path(), "Bash is not installed")
    def test_bash_launcher_runs_from_another_directory(self):
        with tempfile.TemporaryDirectory(prefix="skill forge ") as directory:
            root = Path(directory)
            result = subprocess.run(
                [bash_path(), str(ROOT / "scripts/install.sh"), "--skills-dir", str(root / "skills")],
                cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30,
                env={**os.environ, "PYTHON": Path(sys.executable).as_posix(), "PYTHONUTF8": "1",
                     "HOME": str(root), "USERPROFILE": str(root)},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((root / "skills/skill-forge/SKILL.md").is_file())

    def test_existing_install_lock_blocks_install_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            root.mkdir()
            lock = root / ".skill-forge-install.lock"
            lock.write_text("another installer")
            with self.assertRaises(FileExistsError):
                install.install(root, force=True)
            self.assertEqual(lock.read_text(), "another installer")
            self.assertFalse((root / "skill-forge").exists())

    def test_concurrent_install_is_not_overwritten_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            target = root / "skill-forge"
            copytree = install.shutil.copytree
            def concurrent_copy(*args, **kwargs):
                if not target.exists():
                    target.mkdir()
                    (target / "SKILL.md").write_text("concurrent install")
                return copytree(*args, **kwargs)
            with patch.object(install.shutil, "copytree", side_effect=concurrent_copy):
                with self.assertRaises(FileExistsError):
                    install.install(root)
            self.assertEqual((target / "SKILL.md").read_text(), "concurrent install")

    def test_complete_bundle_runs_outside_checkout_and_replacement_is_safe(self):
        with tempfile.TemporaryDirectory(prefix="skill forge ") as directory:
            base = Path(directory)
            skills = base / "skills"
            command = [sys.executable, str(ROOT / "scripts/install.py"), "--skills-dir", str(skills)]
            env = {**os.environ, "HOME": str(base), "USERPROFILE": str(base), "PYTHONUTF8": "1"}
            def run(args):
                return subprocess.run(args, cwd=base, capture_output=True, text=True, encoding="utf-8", env=env)
            result = run(command)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = skills / "skill-forge"
            for relative in ("SKILL.md", "scripts/generate.py", "scripts/quick_validate.py",
                             "scripts/skill_common.py", "templates/skill-template.md", "requirements.txt"):
                self.assertTrue((installed / relative).is_file(), relative)
            result = run([sys.executable, str(installed / "scripts/generate.py"),
                          str(ROOT / "examples/github-push-input.json"), "--skills-dir", str(skills), "--strict"])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            original = installed / "custom-note.txt"
            original.write_text("keep my modifications")
            self.assertNotEqual(run(command).returncode, 0)
            self.assertTrue(original.is_file())
            self.assertEqual(run(command + ["--force"]).returncode, 0)
            self.assertTrue(any(p.read_text() == "keep my modifications" for p in base.rglob("custom-note.txt")))


class ValidatorTests(unittest.TestCase):
    def check_text(self, text, strict=False):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SKILL.md"
            path.write_text(text, encoding="utf-8")
            return quick_validate.validate(str(path), strict=strict)

    def test_nested_environment_and_delimiter_in_description(self):
        fm, _, body = quick_validate.extract_frontmatter(
            '---\nname: test\ndescription: "Use when --- occurs"\nenvironment:\n  os: Windows\n---\nBody\n')
        self.assertEqual(fm["environment"], {"os": "Windows"})
        self.assertEqual(fm["description"], "Use when --- occurs")
        self.assertIn("Body", body)

    def test_malformed_yaml_and_wrong_types_return_errors(self):
        for raw in ('name: [broken', '- item', 'name: test\ndescription: [bad]',
                    'name: test\ndescription: valid\nenvironment: wrong',
                    'name: first\nname: second\ndescription: valid'):
            with self.subTest(raw=raw):
                errors, _, _ = self.check_text(f"---\n{raw}\n---\nBody")
                self.assertTrue(errors)

    def test_all_unresolved_variables_are_errors(self):
        errors, _, _ = self.check_text("---\nname: test\ndescription: Use when testing things\n---\n{{OS}} {{TRIGGER_1}} {{STEP_8_WHY}}")
        self.assertTrue(any("placeholder" in error.lower() for error in errors))

    def test_unicode_triggers_are_not_one_word_warnings(self):
        _, warnings, _ = self.check_text("---\nname: test\ndescription: Use when pushing code from Windows\n---\n## When to use\n- 把项目推送到远程仓库\n")
        self.assertFalse(any("Trigger #" in warning for warning in warnings))

    def test_strict_checks_verification_semantics(self):
        text = "---\nname: test\ndescription: Use when testing from Windows\n---\n## Verification\nEverything should work.\n"
        normal_errors = self.check_text(text)[0]
        strict_errors = self.check_text(text, strict=True)[0]
        self.assertEqual(normal_errors, [])
        self.assertTrue(any("verification" in error.lower() for error in strict_errors))

    def test_strict_rejects_comment_only_commands(self):
        text = generate.fill_template(generate.load_template(), sample())
        text = re.sub(r"```bash\n.*?```", "```bash\n# No command recorded\n```", text, flags=re.DOTALL)
        errors = quick_validate.validate_text(text, strict=True)[0]
        self.assertTrue(any("command" in error.lower() for error in errors))

    def test_fenced_headings_do_not_end_a_section(self):
        data = sample()
        data["QUICK_START_COMMAND_1"] = "cat <<'END'\n## Example heading\nEND"
        text = generate.fill_template(generate.load_template(), data)
        errors, warnings, _ = quick_validate.validate_text(text, strict=True)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_explicit_null_profile_fields_are_invalid_types(self):
        for key in ("environment", "compatibility"):
            errors, _, _ = self.check_text(f"---\nname: test\ndescription: Use when testing from Windows\n{key}: null\n---\nBody")
            self.assertTrue(errors)


class StorageTests(unittest.TestCase):
    def test_failed_atomic_replacement_preserves_original_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            path = skill_common.save_skill("first version", root, "test-skill")
            with patch.object(skill_common.os, "replace", side_effect=OSError("simulated failure")):
                with self.assertRaises(OSError):
                    skill_common.save_skill("second version", root, "test-skill", force=True)
            self.assertEqual(path.read_text(), "first version")
            self.assertFalse(list(path.parent.glob("*.tmp")))
            self.assertTrue(any(p.read_text() == "first version" for p in Path(directory).rglob("*.bak")))

    def test_no_clobber_if_another_writer_wins_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            target = root / "test-skill/SKILL.md"
            link = skill_common.os.link
            def competing_link(source, destination):
                Path(destination).write_text("other writer")
                return link(source, destination)
            with patch.object(skill_common.os, "link", side_effect=competing_link):
                with self.assertRaises(FileExistsError):
                    skill_common.save_skill("new content", root, "test-skill")
            self.assertEqual(target.read_text(), "other writer")

    def test_skill_directory_symlink_cannot_redirect_output(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "skills"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            try:
                (root / "test-skill").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Directory symlinks require permission on this OS")
            with self.assertRaises(ValueError):
                skill_common.save_skill("redirected output", root, "test-skill", force=True)
            self.assertEqual(list(outside.iterdir()), [])


class ExampleTests(unittest.TestCase):
    @unittest.skipUnless(bash_path(), "Bash is not installed")
    def test_example_prerequisite_failures_prevent_push(self):
        data = sample()
        quick_start = "\n".join(data[f"QUICK_START_COMMAND_{i}"] for i in (1, 2, 3))
        for remote, branch_status in (("https://github.com/owner/repo.git", 0),
                                      ("git@github.com:owner/repo.git", 1),
                                      ("git@github.com:owner/one.git\ngit@github.com:owner/two.git", 0)):
            with self.subTest(remote=remote, branch_status=branch_status):
                script = '''git() {
  case "$1" in
    remote) printf '%s\\n' "$TEST_REMOTE" ;;
    symbolic-ref) printf 'topic\\n'; return "$TEST_BRANCH_STATUS" ;;
    rev-parse) printf 'abcd1234\\n' ;;
    push) printf 'PUSH_ATTEMPTED\\n' ;;
  esac
}
connect() { return 0; }
''' + quick_start
                result = subprocess.run([bash_path(), "-c", script], capture_output=True, text=True,
                                        encoding="utf-8", timeout=30,
                                        env={**os.environ, "TEST_REMOTE": remote, "TEST_BRANCH_STATUS": str(branch_status)})
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("PUSH_ATTEMPTED", result.stdout)


if __name__ == "__main__":
    unittest.main()
