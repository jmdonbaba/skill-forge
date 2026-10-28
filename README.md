# skill-forge

> Turn agent trial-and-error into reusable Claude Code skills — personalized for **your** OS, **your** shell, and **your** network.
>
> 把 agent 绕过的弯路锻造成可复用的 Claude Code skill——为**你的**系统、**你的** shell、**你的**网络环境量身定制。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## The Problem / 痛点

You ask Claude Code to do something. It tries approach A — fails. Tries B — also fails. Three dead ends later, it finally finds a path that works. Why? Because your Windows 11 (Chinese edition), Git Bash, and GFW-trapped network aren't what the agent expected. Even with built-in memory, an agent can repeat the same dead ends when a remembered workaround lacks evidence or environment checks.

你让 Claude Code 帮你做一件事。它试了 A 方案——失败了。换 B——又失败了。绕了三个弯路之后，终于找到一条能走通的路。为什么会绕路？因为你的 Windows 11 中文版、Git Bash、被墙的网络——这些都不是 agent 预期中的"标准环境"。即使有内置记忆，如果经验缺少证据和环境检查，agent 仍可能重复踩坑。

## The Solution / 方案

**skill-forge** captures the *winning path* after a winding task completes, and generates a personalized Claude Code skill from it. On reuse, the agent can check the recorded environment and verification steps before applying the approach.

**skill-forge** 在 agent 绕完弯路终于成功之后，把那条最终走通的路记录下来，生成一个个性化的 Claude Code skill。下次加载时，agent 可以先核对适用环境和验证步骤，再决定是否复用。

The generated skill records / 生成的 skill 会记录：

- ✅ The exact commands that worked / 实际跑通的命令
- ❌ The dead ends that didn't — and **why** (environment-specific cause) / 失败的做法——以及环境层面的原因
- 🔧 Your environment / 你的运行环境（OS, shell, 网络, 工具版本）
- 🔍 How to verify success / 验证成功的方法
- 🎯 Specific trigger descriptions to evaluate in real sessions / 可在真实会话中评测的触发描述

## Quick Start / 快速开始

### 1. Install the meta-skill / 安装元技能

Requires Python 3.10+ and PyYAML. / 需要 Python 3.10+ 和 PyYAML。

```bash
python -m pip install -r requirements.txt
python scripts/install.py
```

Bash alternative / Bash 下也可使用：`bash scripts/install.sh`。

This installs the complete bundle to `~/.claude/skills/skill-forge/`, including
scripts, template and requirements. Run it from any working directory using
the installer's path. In PowerShell, use `python scripts/install.py`.
安装完整目录，包含脚本、模板和依赖声明；离开仓库也能使用。

Reinstalling refuses to overwrite by default. Use `--force` for an intentional
update; the previous directory (including local edits) is kept under
`~/.claude/skill-forge-backups/`. / 默认不覆盖，显式更新会保留完整备份。

### 2. Generate your first skill / 生成你的第一个 skill

After a winding but successful task, say in Claude Code:
在一次绕了弯路但最终成功的任务之后，在 Claude Code 中说：

```
/skill-forge

I just managed to push my project to GitHub after several failed attempts.
我刚才终于把项目推上 GitHub 了，中间失败了好几次。
```

Claude will analyze the conversation, identify the dead ends, extract the winning path, validate the result, tune the description, and save the skill to `~/.claude/skills/<name>/SKILL.md`.
Claude 会分析对话记录，识别弯路，提取成功路径，验证结果，调整触发描述，然后保存到 `~/.claude/skills/<name>/SKILL.md`。

### 3. Use it / 使用 skill

Test `/<name>` in a fresh Claude Code session, then try a matching prompt and an unrelated prompt. Check environment differences before reusing commands.
在新会话中先测试 `/<name>`，再测试应触发和不应触发的请求；复用命令前核对当前环境。

## Standalone Generator / 独立生成器

For scripting or CI use:

```bash
# Interactive mode
python scripts/generate.py

# From JSON
python scripts/generate.py examples/github-push-input.json

# Dry-run — print to stdout, don't save
python scripts/generate.py examples/github-push-input.json --dry-run

# Generate + validation report (structural errors always block saving)
python scripts/generate.py examples/github-push-input.json --validate

# Strict completeness checks; warnings block saving
python scripts/generate.py examples/github-push-input.json --strict

# Use a separate skills root (also works with the installer)
python scripts/generate.py examples/github-push-input.json --skills-dir ./output/skills

# Intentional replacement, with backup
python scripts/generate.py examples/github-push-input.json --force
```

Names must be portable kebab-case, at most 64 characters; path separators and
reserved names are rejected. Dry-run performs the same validation without
writing files. Existing skills, including legacy `<name>.md` files, are never
silently overwritten. `--force` backs up before replacing `SKILL.md` atomically;
the legacy file is left intact for manual review/migration. Custom skills roots
store backups in their sibling `skill-forge-backups/` directory.
名称校验和结构验证都在写入前完成；默认拒绝覆盖，显式替换先备份。

Input accepts the original numbered fields (for example `TRIGGER_1`,
`STEP_1_COMMAND`) or arrays `triggers`, `quick_start`, `steps`
(`title`, `command`, `why`) and `pitfalls` (`approach`, `why`, `symptom`).
Do not mix both formats for the same collection. All entries are retained;
interactive entry ends with an empty line rather than a fixed item cap.
旧 JSON 格式继续兼容，也支持数组；所有触发词、步骤和失败记录均完整保留。

## Quick Validator / 快速验证

Check any skill file for common issues:

```bash
python scripts/quick_validate.py ~/.claude/skills/github-push/SKILL.md
python scripts/quick_validate.py ~/.claude/skills/github-push/SKILL.md --strict
```

Uses PyYAML safe parsing (including duplicate-key rejection) and explicit type
checks for the Skill Forge profile: `name`, `description`, `compatibility`, and
`environment.os/shell/network/tools`. The last two are Forge conventions, not
required Claude Code fields. All unresolved template variables are errors.

`--strict` also checks directory/name consistency for `SKILL.md`, balanced code
fences, command sections, and a verification command with expected output;
warnings cause a nonzero exit. Trigger/command wording hints remain heuristics,
not evidence of correct routing or execution. No command in a skill is executed
by this validator. See [behavioral evaluation](docs/validation.md) for real
positive/negative task tests and the limits of static checks.

使用真实 YAML 解析和字段类型检查；严格模式额外检查内容完整性。
静态验证不代表 Claude 已实际加载、正确触发或成功执行。

Layout and resource resolution follow the [Claude Code skills documentation](https://code.claude.com/docs/en/skills).

## Example / 示例

An illustrative Git Bash + HTTP CONNECT proxy example / Git Bash 与 HTTP CONNECT 代理说明性示例：

- SSH receives its proxy through `ProxyCommand`; Git `http.proxy` applies to HTTP(S).
- Inspect the existing `origin` and current local branch; do not assume `main` or `master`.
- Confirm remote commit identity after pushing; listing remote refs alone is insufficient.
- Verify the proxy protocol/port, helper availability and SSH key locally first.

The corrected example is a documentation fixture, not a claimed successful
network run. It requires an existing SSH remote and commits; it does not create
a GitHub repository. / 修正后的示例不冒充已实测经验，也不负责创建远程仓库。

→ [Generated skill / 生成示例](examples/github-push.md)
→ [JSON input / JSON 输入](examples/github-push-input.json)

## How It Works / 工作流程

```
绕弯路的对话记录
        │
        ▼
  ┌─────────────┐
  │ 1. GATHER    │  任务是什么？哪些失败了？为什么？（环境原因！）
  │    收集      │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 2. CONFIRM   │  向用户确认摘要 —— 错误的 skill 比没有更糟
  │    确认      │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 3. GENERATE  │  填入环境 + 踩坑记录 + 成功路径
  │    生成      │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 4. VALIDATE  │  自动检查占位符、缺失字段、弱触发词
  │    验证      │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 5. TUNE      │  优化 description 确保 skill 可靠触发
  │    调优      │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ 6. INSTALL   │  保存到 ~/.claude/skills/<name>/SKILL.md
  │    安装      │
  └─────────────┘
```

## Generated Skill Anatomy / Skill 结构

Every skill generated by skill-forge includes / 每个 skill 包含：

| Section / 章节 | Purpose / 用途 |
|----------|---------|
| **Environment** / 环境 | OS, shell, network, tools — so the agent knows *where* it's running / 让 agent 知道自己在什么环境下运行 |
| **When to use** / 触发条件 | Natural trigger phrases that activate the skill / 触发 skill 的自然语言短语 |
| **Quick start** / 快速上手 | Minimal commands with explicit prerequisites / 带明确前提的最简命令路径 |
| **Proven approach** / 可行方案 | Step-by-step commands + the *why* / 逐条命令 + 每一步的环境原因 |
| **Pitfalls** / 避坑指南 | Failed attempts, their environment causes, and symptoms / 失败的做法、环境原因、具体表现 |
| **Verification** / 验证 | How to confirm success + expected output / 验证命令 + 预期输出 |

## Comparison with skill-creator / 与 skill-creator 的对比

This project complements Anthropic's official [skill-creator](https://skills.sh/anthropics/skills/skill-creator).

| | skill-forge | skill-creator (Anthropic) |
|---|---|---|
| 入口 | 事后：刚完成一个绕了 N 次弯路才成功的任务 | 事前：想设计一个全新的 skill |
| 流程 | 从对话提取 → 一次性生成 | 草拟 → eval 跑分 → 迭代改进 |
| 重点 | 环境特化的踩坑记录 | 通用的 skill 设计方法 |
| 验证 | 用户确认 + quick_validate.py | 并行 subagent 对比 + 量化 benchmark + blind A/B |

skill-forge 和 skill-creator 互补不冲突。用 skill-forge 把踩坑经验固化为 skill，用 skill-creator 从零设计全新 skill 或做 eval 驱动的迭代优化。

## Project Structure / 项目结构

```
skill-forge/
├── SKILL.md                          # 核心 skill 定义（被安装到 ~/.claude/skills/）
├── CLAUDE.md                         # 项目上下文（Claude Code 进入目录时加载）
├── templates/
│   └── skill-template.md             # 动态生成模板（frontmatter 始终在第一行）
├── scripts/
│   ├── install.sh                    # 一键安装脚本
│   ├── generate.py                   # 独立生成器（交互式 / JSON 输入 / dry-run / validate）
│   ├── install.py                    # 跨平台完整安装与备份
│   ├── skill_common.py               # 路径、YAML 与安全写入
│   └── quick_validate.py             # Skill 质量检查器（YAML / 占位符 / 触发词 / 描述）
├── examples/
│   ├── github-push.md                # 示例：生成的 skill 长什么样
│   └── github-push-input.json        # 示例：JSON 输入格式
├── requirements.txt                 # PyYAML 依赖
├── tests/                           # 回归与安装集成测试
├── docs/                            # 验证方法与后续路线图
└── LICENSE
```

## What Makes a Good Skill / 什么值得生成 skill

Worth it / 值得：

- ✅ Proxy, mirrors, PATH quirks / 代理、镜像源、PATH 等环境问题
- ✅ Platform differences (Windows vs macOS vs Linux) / 平台差异
- ✅ Shell-specific syntax (Git Bash vs PowerShell vs zsh) / Shell 差异
- ✅ Toolchain bugs or version-specific behavior / 工具链 bug 或版本特有问题
- ✅ Permission, firewall, admin-rights / 权限、防火墙、管理员权限

Not worth it / 不值得：

- ❌ One-off tasks / 不会再做的一次性任务
- ❌ Generic solutions in official docs / 官方文档里已经写清楚的
- ❌ Tasks that worked first try with no dead ends / 一次就成功的任务（没什么好记录的）

## Tests and roadmap / 测试与路线图

```bash
python -m unittest discover -s tests -v
python scripts/quick_validate.py examples/github-push.md --strict
```

A [GitHub Actions template](ci/github-actions-tests.yml) runs this suite on
Windows, macOS and Linux, Python 3.10 and 3.13. To enable it, copy the template
to `.github/workflows/tests.yml` and push using a credential with `workflow`
permission. The current GitHub login cannot create workflow files, so the
template is provided without enabling CI.
提供跨平台 CI 模板；当前登录缺少 workflow 权限，尚未启用自动运行。
The suite uses temporary user/skills directories and never executes generated
Git push commands. [Validation guide](docs/validation.md) distinguishes local
automation from Claude Code integration checks.

The experience-management and learning-system ideas from the review are
tracked in the [roadmap](docs/roadmap.md), with acceptance criteria. Automated
merge/deduplication, hooks, rescue recommendations and A/B reporting are planned
work; the current tools generate and statically validate skills.
经验管理、自动发现和效果度量见路线图；当前实现不宣称具备这些能力。

## Contributing / 贡献

Found a pattern that skill-forge doesn't handle well? Have an environment-specific example to share? PRs welcome — especially examples that help developers in similar setups.
发现了 skill-forge 没覆盖到的场景？有特定环境的踩坑经验？欢迎 PR——尤其欢迎能帮助同类环境开发者的示例。

## License / 协议

MIT — see [LICENSE](LICENSE).
