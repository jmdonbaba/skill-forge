# Validation and evidence

## Automated checks

Requires Python 3.10+ and `python -m pip install -r requirements.txt`.

```bash
python -m unittest discover -s tests -v
python scripts/quick_validate.py examples/github-push.md --strict
```

The regression suite exercises both JSON and interactive generation, nested and
invalid YAML, unsafe names, all collected entries, dry-run, replacement backups,
strict-mode failures and installation in paths containing spaces. The installer
test runs the installed generator and Bash launcher from outside the checkout.
Fake Git commands also confirm that failed example prerequisites cannot reach
the push command; these are shell control-flow tests, not network evidence. User home and
skills directories are isolated. It does not push to GitHub or execute commands
from generated skills. The template in `ci/github-actions-tests.yml` configures the same suite on
three OSes. CI is not enabled: the current GitHub OAuth credential lacks the
`workflow` scope. To activate, copy it to `.github/workflows/tests.yml` and push
with a credential allowed to modify workflows.

Normal validation parses YAML safely and checks explicit field types. It flags
every unresolved template variable, including in frontmatter. Missing Forge
profile fields or sections produce warnings; wrong types produce errors.
`environment` and `compatibility` are Forge conventions, not mandatory fields in
the Claude Code format. Additional frontmatter fields are allowed.

Strict validation additionally checks canonical directory/name agreement when
the filename is `SKILL.md`, complete command sections, balanced code fences,
and a verification command with non-empty expected output. It requires the
Forge environment profile. The CLI fails on errors, and in strict mode on
warnings. Generation always rejects structural errors before writing, including
without `--validate`; `--validate` prints the report. Dry-run uses the same
checks and writes nothing.

These checks cannot establish command safety, correctness, causal explanations,
environment compatibility, or model trigger behavior. Expected output is a test
criterion, not evidence that the output was actually observed.

## Real Claude Code integration checks

After installation, start a fresh local Claude Code session in another project:

1. Confirm `/skill-forge` is listed and can be invoked. Ask it to open its
   bundled template and validator. Their paths must be inside the installed
   skill, even when the checkout is elsewhere or unavailable.
2. Capture a completed task with actual command/output evidence. Preview the
   candidate, review every command and environment precondition, then generate
   and strictly validate it. Restart the session and invoke the new `/<name>`.
3. Run the positive and negative prompts in `examples/github-push-evals.json`
   against a disposable repository. Do not automatically run the illustrative
   proxy configuration on a live project. The example needs a reachable HTTP
   CONNECT proxy, an available `connect` helper, authorized SSH key and an
   existing SSH remote. Review host keys normally.
4. For each prompt, record Claude Code/model versions, loaded skills,
   environment, whether the skill loaded, whether prerequisites were checked,
   success/failure, retries, tool calls and time. Use fresh sessions to avoid
   conversation-history bias. Negative prompts must not cause an SSH push.
5. Compare actual remote branch OID with local HEAD to prove push completion.
   Network access or a zero-exit read-only query alone is insufficient.

Do not label a skill verified until its intended task passed with preserved
evidence. No interactive Claude Code discovery/routing test or live proxy push
is claimed by the automated suite. The JSON cases are evaluation fixtures, not
an automated model judge or a reported pass rate.

## Evidence and maintenance

Installations serialize through `.skill-forge-install.lock` in the chosen
skills root. An interrupted process may leave this lock behind: first confirm
no installer is running, then remove that specific stale lock and retry.
Explicit bundle replacement backs up all resources and local edits; a failed
publication restores the previous bundle when the target is still absent.

Keep the failed command, observed error, hypothesized cause, successful action
and verification output separate. Redact credentials and private repository
details before recording experience. A later successful attempt does not by
itself prove why an earlier attempt failed.

Before reuse, compare relevant tool versions, shell, proxy protocol/port and
remote transport. A mismatch calls for investigation, not automatic execution
of an old workaround. This release provides instructions for that check;
automated environment fingerprints and evidence lifecycle are roadmap items.

See the [official skill layout and resource documentation](https://code.claude.com/docs/en/skills),
[Git HTTP proxy configuration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-httpproxy),
[Git push refspec rules](https://git-scm.com/docs/git-push), and
[OpenSSH ProxyCommand](https://man.openbsd.org/ssh_config#ProxyCommand).
