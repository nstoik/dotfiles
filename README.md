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
```
## Nerdfonts
TODO: Add instructions for installing nerdfonts

* [GitHub repo](https://github.com/ryanoasis/nerd-fonts)
* [CascadiaCode Font](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/CascadiaCode)
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
* [ssh authorized_keys](ssh/authorized_keys) to `~/.ssh/authorized_keys`
    * This file is used to store the authorized_keys that are allowed to connect to the computer over ssh.
    * This file will not be linked if the environment variable `DOTBOT_SKIP_SSH_AUTHORIZED_FILE` is set.
    * eg. `DOTBOT_SKIP_SSH_AUTHORIZED_FILE=1 ./install-standalone ssh` will skip linking the authorized_keys file.
    * otherwise the file linking will be forced and overwrite the existing file if it exists.



```


# Git
The [git config](meta/configs/git.yaml) will link the following files:
* [gitconfig](git/gitconfig) to `~/.gitconfig`

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
├── git.yaml
├── ssh-confd.yaml
├── ssh.yaml
└── zsh.yaml
```
## Dotfiles
```
.
├── README.md
├── install-profile
├── install-standalone
├── shells
│   ├── bash
│   │   └── bashrc
│   └── zsh
│       ├── p10k.zsh
│       └── zshrc
├── ssh
│   ├── authorized_keys
│   ├── config
│   ├── known_hosts_fixed
└── tools
    └── git
        └── gitconfig
```