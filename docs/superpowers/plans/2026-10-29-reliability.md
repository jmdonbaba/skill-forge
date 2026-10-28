# Skill Forge reliability implementation plan

**Goal:** Resolve the concrete defects in the supplied review and push verified fixes.

**Architecture:** Share skill naming, YAML parsing and safe file writing between the generator, validator and installer. Keep structural checks local and deterministic; document real Claude Code behavior checks separately.

**Tech stack:** Python 3.10+, PyYAML 6, unittest, Bash launcher, GitHub Actions.

## Constraints

- Install and generate `<skills-dir>/<name>/SKILL.md` with frontmatter on line one.
- Preserve existing indexed JSON inputs and every collected trigger, step and pitfall.
- Reject invalid names, unresolved variables and invalid input before writing.
- Refuse overwrites by default; explicit replacement preserves backups.
- No unverified claims of task success or automatic trigger accuracy.
- Product ideas in sections II–VI of the review are a roadmap, not existing defects.

## Tasks

1. Add failing regression tests in `tests/test_tools.py` for output layout, frontmatter, full collection retention, YAML/schema failures, overwrite protection and validation exit codes. Run `python -m unittest discover -s tests -v` to reproduce the failures.
2. Add `scripts/skill_common.py` for name validation, safe YAML and atomic writing. Update `scripts/generate.py`, `templates/skill-template.md`, `scripts/quick_validate.py` and `requirements.txt`. Re-run the regression suite.
3. Add `scripts/install.py` and update `scripts/install.sh` to install the complete bundle with replacement backups. Test installation and generation from a different working directory in temporary folders, without changing personal skills.
4. Correct the GitHub example and input, update `SKILL.md`, `CLAUDE.md` and `README.md`, document behavioral evals and the experience-learning roadmap, and add cross-platform CI.
5. Run full tests, strict validation of the example, installer smoke tests and diff checks. Request an independent code review, fix actionable findings, commit and push to the tracked remote branch without force.

## Validation result

Implementation and independent review are complete. The local suite ran 29
checks: 28 passed; the directory-symlink case was skipped because Windows
requires additional symlink permission. Strict example validation and diff
whitespace checks passed. The Bash launcher and installed generator were
exercised outside the checkout. Live Claude Code routing was not tested.

GitHub rejected the first push because the OAuth credential lacks `workflow`
permission. The CI configuration is therefore delivered as
`ci/github-actions-tests.yml`, with activation instructions, rather than as an
enabled workflow. All code and local tests remain included in the push.
