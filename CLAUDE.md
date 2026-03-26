# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a dotfiles repository managed by [Dotbot](https://github.com/anishathalye/dotbot) in "advanced mode" supporting multiple host profiles. It symlinks configuration files from this repo into the home directory.

## Installation Commands

Initial setup:
```bash
git clone https://github.com/nstoik/dotfiles.git --recursive
cd dotfiles
sudo chmod +x install-profile install-standalone
```

After pulling updates, sync submodules:
```bash
git submodule update --init
```

Install a predefined profile:
```bash
./install-profile <profile>        # e.g., server or workstation
```

Install individual configs:
```bash
./install-standalone <configs...>  # e.g., ssh zsh git
./install-standalone ssh-confd-sudo  # add -sudo suffix for elevated privileges
```

Remove all symlinks for a profile (e.g. before switching profiles):
```bash
./uninstall-profile <profile>
```

All install commands are safe to run multiple times (`relink: true` is set globally).

## Architecture

### Profile System

- `meta/profiles/` — profile files listing which configs to apply (`client`, `server`, `workstation`)
- `meta/configs/` — individual YAML config files consumed by Dotbot
- `meta/base.yaml` — global Dotbot defaults (`relink: true`, `clean: ['~']`)
- `meta/dotbot/` — Dotbot v1.24.0 as a git submodule

### Managed Configurations

| Config | Source | Destination |
|--------|--------|-------------|
| `zsh.yaml` | `shells/zsh/zshrc`, `shells/zsh/p10k.zsh` | `~/.zshrc`, `~/.p10k.zsh` |
| `bash.yaml` | `shells/bash/bashrc` | `~/.bashrc` |
| `git.yaml` | `tools/git/gitconfig` | `~/.gitconfig` |
| `ssh.yaml` | `ssh/config`, `ssh/known_hosts_fixed` | `~/.ssh/config`, `~/.ssh/known_hosts_fixed` |
| `ssh-authorized.yaml` | `ssh/authorized_keys` | `~/.ssh/authorized_keys` |
| `ssh-known-hosts-ansible.yaml` | `ssh/known_hosts_ansible` | `~/.ssh/known_hosts_ansible` |
| `ssh-confd.yaml` | SSH daemon override config | `/etc/ssh/sshd_config.d/` (requires sudo) |
| `claude.yaml` | `claude/settings.json`, `claude/CLAUDE.md`, `claude/statusline-command.sh` | `~/.claude/...` |

### Zsh Setup

The zshrc uses [zsh-snap](https://github.com/marlonrichert/zsh-snap) as a plugin manager that auto-downloads plugins on first use. Plugins include: Powerlevel10k (prompt), zsh-autocomplete, zsh-autosuggestions, zsh-syntax-highlighting, and oh-my-zsh plugins (docker, git, sudo, history).

**WSL2 Bitwarden SSH Agent Bridge**: On WSL2 hosts, zshrc bridges the Bitwarden Desktop SSH agent via `socat` + `npiperelay.exe` instead of the omz `ssh-agent` plugin. Prerequisites: `socat` installed in WSL2, `npiperelay.exe` on the Windows PATH, Bitwarden Desktop with SSH agent enabled.

### SSH known_hosts Strategy

Three separate known_hosts files are merged via SSH `Include`:
- `known_hosts` — live/auto-updated by SSH
- `known_hosts_fixed` — manually maintained in this repo
- `known_hosts_ansible` — managed by the infrastructure repo (applied via `ssh-known-hosts-ansible` config)

## Adding a New Config

1. Create the source file(s) in an appropriate directory (`shells/`, `ssh/`, `tools/`, etc.)
2. Create `meta/configs/<name>.yaml` with `link` directives pointing to those files
3. Add the config name to the relevant profile(s) in `meta/profiles/`
