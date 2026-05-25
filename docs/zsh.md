# ZSH Configuration

ZSH needs to be installed on the computer.

The installed `.zshrc` uses [zsh-snap](https://github.com/marlonrichert/zsh-snap) as a plugin manager that downloads plugins automatically on first use.

The [zsh config](../meta/configs/zsh.yaml) links the following files:
* [zshrc](../shells/zsh/zshrc) to `~/.zshrc`
* [p10k.zsh](../shells/zsh/p10k.zsh) to `~/.p10k.zsh`
* [starship.toml](../shells/starship/starship.toml) to `~/.config/starship.toml`

## Nerd Fonts

The shell prompt requires a [Nerd Font](https://www.nerdfonts.com/) for icons and powerline glyphs. The recommended font is **JetBrainsMono Nerd Font Mono**.

Download from the [nerd-fonts releases page](https://github.com/ryanoasis/nerd-fonts/releases) (`JetBrainsMono.zip`) and install on your system. On Windows, install the font for all users so it is available in WSL2 terminals, then set your terminal to use `JetBrainsMono Nerd Font Mono`.

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

Starship configuration lives in `shells/starship/starship.toml` and is symlinked to `~/.config/starship.toml` by dotbot. The theme uses catppuccin-mocha colors with powerline segments.
