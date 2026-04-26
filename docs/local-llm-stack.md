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
2. In Ollama tray icon → Settings:
   - Enable **"Expose Ollama to network"**
   - Set **Model storage path** to `D:\Ollama` (keeps large model files off the system drive)
3. Pull models (or use `ollama-sync.sh` from WSL2/Linux — see below):
   ```
   ollama pull deepseek-r1:8b
   ollama pull llama3.1:8b
   ollama pull llama3.2:latest
   ollama pull nomic-embed-text:latest
   ollama pull qwen2.5-coder:1.5b
   ollama pull qwen2.5-coder:1.5b-base
   ollama pull qwen2.5-coder:7b
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

**Windows (including WSL2 sessions):** `C:\Users\nelson\.continue\config.yaml`
→ source: `tools/continue/config.windows.yaml` — uses `localhost:11434`

Continue is a UI extension and always runs on the Windows side, even when VSCode is connected to WSL2. The Windows config is always active on this machine. Copy manually whenever the source changes:

```bash
cp ~/GitHub/dotfiles/tools/continue/config.windows.yaml /mnt/c/Users/nelso/.continue/config.yaml
```

**Linux-native machines (laptop etc.):** `~/.continue/config.yaml`
→ managed via dotbot: `./install-profile workstation` symlinks `tools/continue/config.lan.yaml` — uses `10.10.1.100:11434`

---

## Models Reference

| Model | Size | Purpose |
|---|---|---|
| `qwen2.5-coder:14b` | ~8.7 GB | Chat / code assistance (Continue chat, Open WebUI) + PR review (default) |
| `qwen2.5-coder:1.5b-base` | ~1.0 GB | Tab autocomplete in Continue (base model) |
| `nomic-embed-text:latest` | ~270 MB | Embeddings for Open WebUI |
| `deepseek-r1:8b` | ~4.9 GB | Reasoning / alternative PR review model |
| `llama3.1:8b` | ~4.9 GB | General chat in Open WebUI |
| `llama3.2:latest` | ~2.0 GB | General chat in Open WebUI (smaller/faster) |

---

## PR Review Script

`bin/pr-review.sh` sends a PR diff to Ollama for a code review (default model: `qwen2.5-coder:14b`).

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
- `qwen2.5-coder:14b` has a 32K context window, but very large diffs may still be truncated or produce degraded output. Split large PRs into reviewable chunks.
- The review has no knowledge of the broader codebase — it only sees the diff.

---

## Model Sync Script

`bin/ollama-sync.sh` pulls/updates all models listed in `~/ai/models.txt` and removes any installed models not in that list.

**Usage:**
```bash
ollama-sync.sh
```

**How it works:**
- Pulls each listed model (no-op if already up to date; downloads new layers if the tag was updated)
- Queries the Ollama API for currently installed models and removes any not in the list

**To add or remove a model**, edit `ai/models.txt` and re-run the script.

**Requirements:** `curl` and `jq` must be on PATH. `OLLAMA_BASE_URL` must be set (exported in zshrc).

---

## Future Work

- **Continue codebase awareness:** Add `.continue/rules/*.md` files with project architecture and coding standards so the Continue agent has codebase context. See [docs](https://docs.continue.dev/guides/codebase-documentation-awareness).
- **Automated PR review comments:** Pipe `pr-review.sh` output through `gh pr comment` to post the review directly on the GitHub PR.
