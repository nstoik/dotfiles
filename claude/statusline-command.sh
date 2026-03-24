#!/bin/sh
# Claude Code status line — mirrors p10k prompt: user@host dir [git] | model ctx%
input=$(cat)

user=$(whoami)
host=$(hostname -s)
dir=$(echo "$input" | jq -r '.workspace.current_dir')

# Shorten home directory to ~
home_dir="$HOME"
short_dir="${dir#$home_dir}"
if [ "$short_dir" != "$dir" ]; then
  short_dir="~$short_dir"
else
  short_dir="$dir"
fi

# Git branch and dirty status (skip optional locks)
git_info=""
if git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
  branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null || git -C "$dir" rev-parse --short HEAD 2>/dev/null)
  dirty=$(git -C "$dir" status --porcelain --no-lock-index 2>/dev/null | head -1)
  if [ -n "$dirty" ]; then
    git_info=" [$branch *]"
  else
    git_info=" [$branch]"
  fi
fi

# Model and context
model=$(echo "$input" | jq -r '.model.display_name')
ctx=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$ctx" ]; then
  ctx_display=" | ctx:$(printf '%.0f' "$ctx")%"
else
  ctx_display=""
fi

printf '%s@%s %s%s | %s%s' "$user" "$host" "$short_dir" "$git_info" "$model" "$ctx_display"
