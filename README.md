# Dotfiles for Nelson

This repository contains all the dotfiles I use on my computers. 

This setup uses [dotbot](https://github.com/anishathalye/dotbot) to manage the dotfiles. 

[Dotbot Blog for setup](https://www.elliotdenolf.com/posts/bootstrap-your-dotfiles-with-dotbot)

It is configured in the [advanced mode](https://github.com/anishathalye/dotbot/wiki/Tips-and-Tricks#how-can-i-have-different-groups-of-tasks-for-different-hosts-with-different-configurations) to be able to run different configurations for different hosts.

# Installation
``` bash
> git clone https://github.com/nstoik/dotfiles.git --recursive
> cd dotfiles
> sudo chmod +x install-profile install-standalone uninstall-profile
> chmod +x meta/dotbot/bin/dotbot
```

`uninstall-profile` requires Python 3 and PyYAML. Install PyYAML with:
``` bash
pipx install pyyaml
```

After pulling updates on any machine, run the following to sync submodules to the correct commit:
``` bash
git submodule update --init
```
## Nerd Fonts

The shell prompt (Starship or Powerlevel10k) requires a [Nerd Font](https://www.nerdfonts.com/) for icons and powerline glyphs. The recommended font is **JetBrainsMono Nerd Font Mono**.

Download from the [nerd-fonts releases page](https://github.com/ryanoasis/nerd-fonts/releases) (`JetBrainsMono.zip`) and install on your system. On Windows, install the font for all users so it is available in WSL2 terminals, then set your terminal to use `JetBrainsMono Nerd Font Mono`.
# Usage
For installing a predefined profile:

``` bash
~/.dotfiles$ ./install-profile <profile> [<configs...>]
# see meta/profiles/ for available profiles
```

For installing single configurations:
``` bash
~/.dotfiles$ ./install-standalone <configs...>
# see meta/configs/ for available configurations
```

You can also invoke a single configuration as a sudoer by adding `-sudo` to the end of a configuration name. In the example below, the `some-config` config will be run with elavated privleges, but `some-other-config` will not.
``` bash
~/.dotfiles$ ./install-standalone some-config-sudo some-other-config
```

To remove all symlinks for a profile (e.g. before switching to a different profile):
``` bash
~/.dotfiles$ ./uninstall-profile <profile>
```


You can run these installation commands safely multiple times.

If there are errors when running the install script, it can mean that files you are trying to symlink to are already present. Remove the file in the current directory and try the install script again.

# ZSH
ZSH needs to be installed on the computer.

The installed `.zshrc` uses [zsh-snap](https://github.com/marlonrichert/zsh-snap) as a plugin manager. This will download plugins automatically on first use.

The [zsh config](meta/configs/zsh.yaml) links the following files:
* [zshrc](shells/zsh/zshrc) to `~/.zshrc`
* [p10k.zsh](shells/zsh/p10k.zsh) to `~/.p10k.zsh`
* [starship.toml](shells/starship/starship.toml) to `~/.config/starship.toml`

## Prompt Theme

The prompt can be switched between [Starship](https://starship.rs/) (default) and [Powerlevel10k](https://github.com/romkatv/powerlevel10k) by creating `~/.zshrc.local` (not tracked in this repo):

```zsh
# Use Powerlevel10k instead of Starship
PROMPT_THEME=p10k
```

Remove `~/.zshrc.local` (or leave it empty) to revert to Starship.

**Installing Starship:**
```bash
curl -sS https://starship.rs/install.sh | sh
```

Starship configuration lives in `shells/starship/starship.toml` and is symlinked to `~/.config/starship.toml` by dotbot.

# SSH
The [ssh config](meta/configs/ssh.yaml) will link the following files:
* [ssh config](ssh/config) to `~/.ssh/config`
* [ssh known_hosts_fixed](ssh/known_hosts_fixed) to `~/.ssh/known_hosts_fixed`
    * Manually maintained known hosts.

The [ssh-authorized config](meta/configs/ssh-authorized.yaml) will link:
* [authorized_keys](ssh/authorized_keys) to `~/.ssh/authorized_keys`
    * SSH keys permitted to connect to this machine.

The [ssh-known-hosts-ansible config](meta/configs/ssh-known-hosts-ansible.yaml) will link:
* [known_hosts_ansible](ssh/known_hosts_ansible) to `~/.ssh/known_hosts_ansible`
    * Known hosts managed by Ansible and the [infrastructure repo](https://github.com/nstoik/infrastructure).

## WSL2: Bitwarden SSH Agent Bridge

On WSL2 hosts, the zshrc automatically bridges the Bitwarden Desktop SSH agent into WSL2 instead of using the omz `ssh-agent` plugin. This allows SSH keys managed in Bitwarden to be used from within WSL2.

### Prerequisites

1. **Bitwarden Desktop** must be installed on Windows with the SSH agent enabled:
   - Open Bitwarden Desktop → Settings → SSH Agent → enable "Enable SSH Agent"

2. **`socat`** must be installed in WSL2:
   ``` bash
   sudo apt install socat
   ```

3. **`npiperelay.exe`** must be available on the Windows PATH:
   - Download from [jstarks/npiperelay](https://github.com/jstarks/npiperelay/releases)
   - Place `npiperelay.exe` in `C:\Windows\System32\`

### How it works

On WSL2, zshrc:
- Sets `SSH_AUTH_SOCK` to `~/.ssh/agent.sock`
- Starts a `socat` process (if not already running) that relays the Unix socket to the Windows named pipe `//./pipe/openssh-ssh-agent` used by Bitwarden Desktop
- Skips loading the omz `ssh-agent` plugin (which would conflict)

On non-WSL2 hosts, the omz `ssh-agent` plugin is loaded as normal.

### Testing the Bridge

After opening a new shell (or running `source ~/.zshrc`), verify the bridge is working:

**1. Check the socket exists and socat is running:**
``` bash
ls -la ~/.ssh/agent.sock
pgrep -a socat
```

**2. Confirm `SSH_AUTH_SOCK` is set correctly:**
``` bash
echo $SSH_AUTH_SOCK
# Expected: /home/<user>/.ssh/agent.sock
```

**3. List keys loaded in Bitwarden's SSH agent:**
``` bash
ssh-add -l
```
Expected output: one or more key fingerprints. If you see `The agent has no identities.`, Bitwarden has no SSH keys added. If you see `Error connecting to agent`, the bridge is not working — check that Bitwarden Desktop is running and the SSH agent is enabled.

**4. Test an actual SSH connection** (replace `git@github.com` with any host you have a key for):
``` bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Troubleshooting:**
- If `ssh-add -l` fails, restart the bridge manually:
  ``` bash
  rm -f ~/.ssh/agent.sock
  source ~/.zshrc
  ssh-add -l
  ```
- Ensure Bitwarden Desktop is unlocked and `npiperelay.exe` is on the Windows PATH.
- Verify the named pipe exists from WSL2: `ls /mnt/c/Windows/System32/npiperelay.exe`


# Git
The [git config](meta/configs/git.yaml) will link the following files:
* [gitconfig](git/gitconfig) to `~/.gitconfig`

# Claude Code
The [claude config](meta/configs/claude.yaml) will:
* Create `~/.claude/` if it doesn't exist
* Clean broken symlinks from `~/.claude/`
* Link the following files:
  * [settings.json](claude/settings.json) to `~/.claude/settings.json`
  * [CLAUDE.md](claude/CLAUDE.md) to `~/.claude/CLAUDE.md`
  * [statusline-command.sh](claude/statusline-command.sh) to `~/.claude/statusline-command.sh`

The `statusline-command.sh` script requires the following tools on your `PATH`:
* `git` (for repository status)
* `jq` (for JSON parsing)

# Contents
To create the charts below, run the following commands:
``` bash
tree meta/profiles
tree meta/configs
tree -I 'meta' .
```
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
## Dotfiles
```
.
├── CLAUDE.md
├── README.md
├── claude
│   ├── CLAUDE.md
│   ├── settings.json
│   └── statusline-command.sh
├── install-profile
├── install-standalone
├── shells
│   ├── bash
│   │   └── bashrc
│   ├── starship
│   │   └── starship.toml
│   └── zsh
│       ├── p10k.zsh
│       └── zshrc
├── ssh
│   ├── authorized_keys
│   ├── config
│   ├── known_hosts_ansible
│   └── known_hosts_fixed
└── tools
    └── git
        └── gitconfig
```
