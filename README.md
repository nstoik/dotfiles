# Dotfiles for Nelson

This repository contains all the dotfiles I use on my computers. 

This setup uses [dotbot](https://github.com/anishathalye/dotbot) to manage the dotfiles. 

[Dotbot Blog for setup](https://www.elliotdenolf.com/posts/bootstrap-your-dotfiles-with-dotbot)

It is configured in the [advanced mode](https://github.com/anishathalye/dotbot/wiki/Tips-and-Tricks#how-can-i-have-different-groups-of-tasks-for-different-hosts-with-different-configurations) to be able to run different configurations for different hosts.

## Installation
``` bash
> git clone https://github.com/nstoik/dotfiles.git --recursive
> cd dotfiles
> sudo chmod +x install-profile install-standalone

```
## Usage
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

## ZSH and Oh My ZSH
ZSH and ohmyzsh needs to be installed on the computer.

[ohmyzsh webpage](https://github.com/ohmyzsh/ohmyzsh)

The [zsh config](meta\configs\zsh.yaml) attempts to install ohmyzsh if it is not already present
## SSH and enforcing passwordless login
Passwordless login is enforced by copying the following configuration file.

``` bash
~/.dotfiles$ ./install-standalone ssh-confd-sudo
```

This config is not included in any of the profiles and needs to be run manually. This is because the required ssh keys need to be copied to the server first.

# Contents
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
├── shells
│   ├── bash
│   │   └── bashrc
│   └── zsh
│       └── zshrc
├── ssh
│   ├── authorized_keys
│   ├── config
│   ├── known_hosts_fixed
│   └── sshd
│       └── sshd_custom_override.conf
└── tools
    └── git
        └── gitconfig
```