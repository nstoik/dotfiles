# Local LLM Stack

## Overview

```
Windows Desktop (Ollama + AMD RX 7600 XT 16GB)
    |
    | HTTP :11434
    v
docker-02.home.stechsolutions.ca (Open WebUI container)
    |
    | HTTPS via Traefik
    v
https://openwebui.home.stechsolutions.ca
```

Ollama runs on Windows and is GPU-accelerated. Open WebUI lives in the infra repo on `docker-02` and talks to Ollama over the LAN. Continue (VSCode extension) also talks directly to Ollama.

---

## Windows Setup

1. Install Ollama from https://ollama.com/download
2. In Ollama tray icon → Settings → enable **"Expose Ollama to network"**
3. Pull models:
   ```
   ollama pull llama3.2
   ollama pull qwen2.5-coder:7b
   ollama pull qwen2.5-coder:1.5b-base
   ollama pull nomic-embed-text:latest
   ollama pull deepseek-r1:8b
   ```
4. Verify GPU is in use:
   ```
   ollama ps
   ```
   The output should show your model loaded on the RX 7600 XT.

---

## Open WebUI

Open WebUI is deployed via the infra repo (not this dotfiles repo).

- **Compose template:** `inventories/home/host_vars/docker-02.home.stechsolutions.ca/docker_compose/ai.yaml.j2`
- **URL:** https://openwebui.home.stechsolutions.ca
- **Ollama target:** `http://10.10.1.100:11434` (Windows desktop LAN IP)

To deploy or update:
```bash
ansible-playbook playbooks/hosts_configure.yaml \
  --limit=docker-02.home.stechsolutions.ca \
  --tags=docker.compose
```

---

## Continue VSCode Setup

1. Install the [Continue extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue) in VSCode
2. Copy the appropriate config to the Continue config location:

**Windows:** `C:\Users\nelson\.continue\config.yaml`
→ source: `tools/continue/config.windows.yaml`

**WSL2:** `~/.continue/config.yaml`
→ managed via dotbot: `./install-profile workstation` symlinks `tools/continue/config.wsl2.yaml`

> **Note:** Both the WSL2 and Windows configs point to `10.10.1.100:11434` (the Windows desktop's LAN IP). This works from any machine on the LAN, including laptops and WSL2.

---

## Models Reference

| Model | Size | Purpose |
|---|---|---|
| `qwen2.5-coder:7b` | ~4.7 GB | Chat / code assistance (Continue chat, Open WebUI) |
| `qwen2.5-coder:1.5b-base` | ~1.0 GB | Tab autocomplete in Continue |
| `nomic-embed-text` | ~270 MB | Embeddings for `@codebase` indexing in Continue |
| `deepseek-r1:8b` | ~4.9 GB | PR diff review via `pr-review.sh` |
| `llama3.2` | ~2.0 GB | General chat in Open WebUI |

---

## PR Review Script

`bin/pr-review.sh` sends a PR diff to `deepseek-r1:8b` for a code review.

**Usage:**
```bash
pr-review.sh <PR_NUMBER>
```

**Example:**
```bash
pr-review.sh 42
```

**Requirements:** `jq`, `gh` (GitHub CLI), and `curl` must be on PATH. The script checks for `jq` and `gh` and errors with a helpful message if either is missing; `curl` is assumed present. The script is installed to `~/.local/bin`, which Ubuntu adds to `PATH` automatically when the directory exists (via `/etc/profile`).

**Limitations:**
- `deepseek-r1:8b` has an 8K context window — very large diffs will be truncated or produce degraded output. Split large PRs into reviewable chunks.
- The review has no knowledge of the broader codebase — it only sees the diff.

---

## Future Work

- **WSL2 IP auto-update:** A shell script (e.g. sourced in `.zshrc`) that detects the current Windows host IP and patches `OLLAMA_HOST` and the Continue config on each shell start, so WSL2 IP changes are handled automatically.
- **`@codebase` indexing in Continue:** Enable `nomic-embed-text` embeddings to index the local repo so that PR reviews and chat queries have full codebase context rather than just the diff.
- **OpenClaw setup:** Configure OpenClaw pointing at the local Ollama API for agentic workflows.
- **Automated PR review comments:** Pipe `pr-review.sh` output through `gh pr comment` to post the review directly on the GitHub PR.
