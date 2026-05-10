---
name: {{SKILL_NAME}}
description: >-
  {{ONE_LINE_DESCRIPTION}}. Use whenever the user {{TRIGGER_CONTEXT_HINT}} —
  especially when {{ENVIRONMENT_HINT}}.
compatibility: {{COMPATIBILITY}}
environment:
  os: {{OS}}
  shell: {{SHELL}}
  network: {{NETWORK}}
  tools: {{TOOLS}}
---

# {{SKILL_NAME}}

{{ONE_LINE_DESCRIPTION}}

## Environment

| Key | Value |
|-----|-------|
| OS | {{OS}} |
| Shell | {{SHELL}} |
| Network | {{NETWORK}} |
| Tools | {{TOOLS}} |

Why this matters: {{ENVIRONMENT_WHY}} Without this context, the agent will assume a standard Linux/macOS environment and fail with the same dead ends this skill documents.

## When to use

This skill activates when the user asks to:

- {{TRIGGER_1}}
- {{TRIGGER_2}}
- {{TRIGGER_3}}
- {{TRIGGER_4}}
- {{TRIGGER_5}}

The trigger phrases above cover how real users talk — from formal ("push to a remote repository") to casual ("put this on GitHub"). If a phrase feels unnatural, rewrite it to match how you actually speak.

## Quick start

The most common use case distilled to the minimal path:

```bash
{{QUICK_START_COMMAND_1}}
{{QUICK_START_COMMAND_2}}
{{QUICK_START_COMMAND_3}}
```

{{QUICK_START_NOTE}}

## Proven approach

Steps verified in this environment. Every command below was actually run and succeeded.

### 1. {{STEP_1_TITLE}}

```bash
{{STEP_1_COMMAND}}
```

{{STEP_1_WHY}}

### 2. {{STEP_2_TITLE}}

```bash
{{STEP_2_COMMAND}}
```

{{STEP_2_WHY}}

### 3. {{STEP_3_TITLE}}

```bash
{{STEP_3_COMMAND}}
```

{{STEP_3_WHY}}

## What this skill replaces

Before this skill existed, each session would independently:

1. Try {{BAD_APPROACH_1}} → fail
2. Try {{BAD_APPROACH_2}} → fail
3. Eventually rediscover the winning path

Now the agent loads this skill and jumps straight to the proven approach. No rediscovery needed.

## Pitfalls — what NOT to do

These were tried and failed in this environment. Each one cost real time.

| Dead end | Environment cause | What happened |
|----------|-------------------|---------------|
| {{BAD_APPROACH_1}} | {{WHY_FAILS_1}} | {{FAIL_SYMPTOM_1}} |
| {{BAD_APPROACH_2}} | {{WHY_FAILS_2}} | {{FAIL_SYMPTOM_2}} |
| {{BAD_APPROACH_3}} | {{WHY_FAILS_3}} | {{FAIL_SYMPTOM_3}} |

## Verification

Confirm success with:

```bash
{{VERIFY_COMMAND}}
```

Expected output: {{EXPECTED_OUTPUT}}

## Notes

{{ADDITIONAL_NOTES}}

## See also

{{SEE_ALSO}}
