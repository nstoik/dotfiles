# Dotfiles for Nelson

Dotfiles managed by [Dotbot](https://github.com/anishathalye/dotbot) in [advanced mode](https://github.com/anishathalye/dotbot/wiki/Tips-and-Tricks#how-can-i-have-different-groups-of-tasks-for-different-hosts-with-different-configurations), supporting multiple host profiles.

## Installation

```bash
git clone https://github.com/nstoik/dotfiles.git --recursive
cd dotfiles
sudo chmod +x install-profile install-standalone uninstall-profile
chmod +x meta/dotbot/bin/dotbot
```

`uninstall-profile` requires Python 3 and PyYAML:
```bash
pipx install pyyaml
```

After pulling updates, sync submodules:
```bash
git submodule update --init
```

## Usage

Install a predefined profile:
```bash
./install-profile <profile>        # client, server, or workstation
```

Install individual configs:
```bash
./install-standalone <configs...>  # e.g. ssh zsh git
./install-standalone ssh-confd-sudo  # add -sudo for elevated privileges
```

Remove all symlinks for a profile:
```bash
./uninstall-profile <profile>
```

All install commands are safe to run multiple times.

## Configs

| Config | Details |
|--------|---------|
| `zsh` | ZSH, Starship/p10k prompt — [docs/zsh.md](docs/zsh.md) |
| `ssh` | SSH config, Bitwarden agent bridge — [docs/ssh.md](docs/ssh.md) |
| `claude` | Claude Code settings and skills — [docs/claude.md](docs/claude.md) |
| `git` | gitconfig |
| `bash` | bashrc |

## Local LLM Stack

See [docs/local-llm-stack.md](docs/local-llm-stack.md) for the Ollama + Continue setup.

## Profiles

```
meta/profiles
├── client
├── server
└── workstation
```

## Configs

```
meta/configs
├── bash.yaml
├── claude.yaml
├── git.yaml
├── ssh-authorized.yaml
├── ssh-confd.yaml
├── ssh-known-hosts-ansible.yaml
├── ssh.yaml
└── zsh.yaml          # zshrc, p10k.zsh, starship.toml
```
