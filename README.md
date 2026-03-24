# Dotfiles for Nelson

This repository contains all the dotfiles I use on my computers. 

This setup uses [dotbot](https://github.com/anishathalye/dotbot) to manage the dotfiles. 

[Dotbot Blog for setup](https://www.elliotdenolf.com/posts/bootstrap-your-dotfiles-with-dotbot)

It is configured in the [advanced mode](https://github.com/anishathalye/dotbot/wiki/Tips-and-Tricks#how-can-i-have-different-groups-of-tasks-for-different-hosts-with-different-configurations) to be able to run different configurations for different hosts.

# Installation
``` bash
> git clone https://github.com/nstoik/dotfiles.git --recursive
> cd dotfiles
> sudo chmod +x install-profile install-standalone
> chmod +x meta/dotbot/bin/dotbot
```

After pulling updates on any machine, run the following to sync submodules to the correct commit:
``` bash
git submodule update --init
```
## Nerdfonts

Download and install the [CascadiaCode Nerd Font](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/CascadiaCode) from the [nerd-fonts releases page](https://github.com/ryanoasis/nerd-fonts/releases) and install it on your system. On Windows, install the font for all users so it is available in WSL2 terminals.
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


You can run these installation commands safely multiple times.

If there are errors when running the install script, it can mean that files you are trying to symlink to are already present. Remove the file in the current directory and try the install script again.

# ZSH
ZSH needs to be installed on the computer.

The installed .zshrc file uses [zsh-snap](https://github.com/marlonrichert/zsh-snap). This will download the plugins as needed.

The [zsh config](meta/configs/zsh.yaml) will link the following files:
* [zshrc](zsh/zshrc) to `~/.zshrc`
* [p10k.zsh](zsh/p10k.zsh) to `~/.p10k.zsh`

# SSH
The [ssh config](meta/configs/ssh.yaml) will link the following files:
* [ssh config](ssh/config) to `~/.ssh/config`
* [ssh known_hosts_fixed](ssh/known_hosts_fixed) to `~/.ssh/known_hosts_fixed`
    * This file is used to store the known_hosts that is manually maintained.
* [ssh known_hosts_ansible](ssh/known_hosts_ansible) to `~/.ssh/known_hosts_ansible`
    * This file is used to store the known_hosts_ansible file that is managed by ansible and my [infrastructure repo](https://github.com/nstoik/infrastructure)
    * This file will not be linked if the environment variable `DOTBOT_SKIP_SSH_KNOWN_HOSTS_ANSIBLE_FILE` is set.
* [ssh authorized_keys](ssh/authorized_keys) to `~/.ssh/authorized_keys`
    * This file is used to store the authorized_keys that are allowed to connect to the computer over ssh.
    * This file will not be linked if the environment variable `DOTBOT_SKIP_SSH_AUTHORIZED_FILE` is set.

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

## Examples
``` bash
# Normal installation
~/.dotfiles$ ./install-standalone ssh

# Skipping the Known_hosts_ansible file
~/.dotfiles$ DOTBOT_SKIP_SSH_KNOWN_HOSTS_ANSIBLE_FILE=1 ./install-standalone ssh

# Skipping the authorized_keys file
~/.dotfiles$ DOTBOT_SKIP_SSH_AUTHORIZED_FILE=1 ./install-standalone ssh

# Skipping both files
~/.dotfiles$ DOTBOT_SKIP_SSH_KNOWN_HOSTS_ANSIBLE_FILE=1 DOTBOT_SKIP_SSH_AUTHORIZED_FILE=1 ./install-standalone ssh

```


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
├── server
└── workstation
```
## Configs
```
meta/configs
├── bash.yaml
├── claude.yaml
├── git.yaml
├── ssh-confd.yaml
├── ssh.yaml
└── zsh.yaml
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
