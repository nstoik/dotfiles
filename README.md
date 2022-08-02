# Dotfiles for Nelson

This repository contains all the dotfiles I use on my computers. 

This setup uses dotbot to manage the dotfiles. 

[Dotbot GitHub repo](https://github.com/anishathalye/dotbot)  
[Dotbot Blog for setup](https://www.elliotdenolf.com/posts/bootstrap-your-dotfiles-with-dotbot)

## Setup
``` bash
> git clone https://github.com/nstoik/dotfiles.git --recursive
> cd dotfiles
> sudo chmod +x install
> ./install

```

If there are errors when running the install script, it can mean that files you are trying to symlink to are already present. Remove the file in the current directory and try  the install script again.

## ZSH and Oh My ZSH
ZSH and ohmyzsh needs to be installed on the computer

[ohmyzsh](https://github.com/ohmyzsh/ohmyzsh)

## SSH
Configures the SSH authorized_keys file and the SSH config file
