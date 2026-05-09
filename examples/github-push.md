---
name: github-push
description: Push a local project to GitHub from Windows + China network environment
tags: [windows, china, git-bash, github, proxy, network]
environment:
  os: Windows 11 China
  shell: Git Bash
  network: GFW-restricted (GitHub blocked/delayed)
  tools: git, ssh, clash-verge/v2ray
---

# github-push

Push a local project to a new GitHub repository. Handles network restrictions (GFW), SSH configuration, and Windows-specific path/credential issues.

## Environment

- OS: Windows 11 (Chinese edition)
- Shell: Git Bash (mingw64)
- Network: GitHub intermittently blocked; requires proxy
- Proxy: Clash Verge (default HTTP proxy on 127.0.0.1:7890)

## When to use

Trigger when the user asks to:
- "push to GitHub"
- "upload this project to GitHub"
- "create a GitHub repo for this"
- "put this on GitHub"

## Proven approach

This approach has been verified in this environment:

### Step 1: Configure git proxy (one-time per shell session)
```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```
Without this, `git push` will hang or timeout because GitHub is blocked.

### Step 2: Use SSH instead of HTTPS for the remote
```bash
git remote add origin git@github.com:USERNAME/REPO.git
```
HTTPS may trigger credential manager popups or 403 errors. SSH with key auth is more reliable through the proxy. Ensure `~/.ssh/config` has:
```
Host github.com
    ProxyCommand connect -H 127.0.0.1:7890 %h %p
```

### Step 3: Push with explicit branch
```bash
git push -u origin main
```
Avoid `git push` without args — Git Bash on Windows may misinterpret the default branch name.

## Pitfalls — what NOT to do

| Dead end | Why it fails in this environment |
|----------|----------------------------------|
| `git push` without proxy config | GitHub is blocked; connection times out after 60s |
| HTTPS remote (`https://github.com/...`) | Triggers Windows credential manager popup; often gets 403 even after login |
| `gh auth login` via browser | Browser-based OAuth flow may fail due to proxy/CORS issues |
| `git push origin master` | New repos default to `main`; `master` push gets rejected |

## Verification

```bash
git ls-remote --heads origin
```
Should show the remote branch without errors. A successful push also confirms with the remote URL output.

## Notes

- The proxy address may differ if using v2ray (usually 127.0.0.1:10809) or other tools
- If SSH key is not set up, generate one first: `ssh-keygen -t ed25519 -C "your@email.com"` then add to GitHub Settings → SSH Keys
- The `connect` tool for ProxyCommand comes with Git Bash; if missing, install `mingw-w64-x86_64-connect` via pacman
