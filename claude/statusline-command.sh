#!/bin/sh
# Claude Code status line — powerline style mirroring the starship prompt
# (catppuccin-mocha palette): user@host | dir | git | model | ctx% | time
input=$(cat)

dir=$(echo "$input" | jq -r '.workspace.current_dir')
model=$(echo "$input" | jq -r '.model.display_name')
ctx=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
five_h_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_h_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_d_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

user=$(whoami)
host=$(hostname -s)

# catppuccin-mocha colors, matching shells/starship/starship.toml
BG_RED="\033[48;2;243;139;168m";      FG_RED="\033[38;2;243;139;168m"
BG_PEACH="\033[48;2;250;179;135m";    FG_PEACH="\033[38;2;250;179;135m"
BG_YELLOW="\033[48;2;249;226;175m";   FG_YELLOW="\033[38;2;249;226;175m"
BG_GREEN="\033[48;2;166;227;161m";    FG_GREEN="\033[38;2;166;227;161m"
BG_SAPPHIRE="\033[48;2;116;199;236m"; FG_SAPPHIRE="\033[38;2;116;199;236m"
BG_LAVENDER="\033[48;2;180;190;254m"; FG_LAVENDER="\033[38;2;180;190;254m"
BG_MAUVE="\033[48;2;203;166;247m";    FG_MAUVE="\033[38;2;203;166;247m"
BG_PINK="\033[48;2;245;194;231m";     FG_PINK="\033[38;2;245;194;231m"
FG_CRUST="\033[38;2;17;17;27m"
RESET="\033[0m"

ARROW=""
ROUND_LEFT=""
ROUND_RIGHT=""

# Shorten home directory to ~, then truncate to last 3 path components
home_dir="$HOME"
short_dir="${dir#$home_dir}"
if [ "$short_dir" != "$dir" ]; then
  short_dir="~$short_dir"
else
  short_dir="$dir"
fi
trunc_dir=$(printf '%s' "$short_dir" | awk -F'/' '{
  n = NF
  if (n <= 3) { print; next }
  out = "\xe2\x80\xa6"
  for (i = n - 2; i <= n; i++) out = out "/" $i
  print out
}')

# rounded head cap
# user@host (host only shown over SSH, matching the starship hostname behavior)
line="${FG_RED}${ROUND_LEFT}${RESET}"

line="${line}${BG_RED}${FG_CRUST}  ${user}"
if [ -n "$SSH_TTY" ] || [ -n "$SSH_CONNECTION" ]; then
  line="${line}@${host}"
fi
line="${line} ${RESET}"
prev_fg="$FG_RED"

# directory
line="${line}${prev_fg}${BG_PEACH}${ARROW}${RESET}"
line="${line}${BG_PEACH}${FG_CRUST} ${trunc_dir} ${RESET}"
prev_fg="$FG_PEACH"

# git branch and dirty status (skip optional locks)
git_in_repo=false
if git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
  git_in_repo=true
  branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null || git -C "$dir" rev-parse --short HEAD 2>/dev/null)
  dirty=$(git --no-optional-locks -C "$dir" status --porcelain 2>/dev/null | head -1)
  if [ -n "$dirty" ]; then
    star=" *"
  else
    star=""
  fi
fi

if [ "$git_in_repo" = true ]; then
  line="${line}${prev_fg}${BG_YELLOW}${ARROW}${RESET}"
  line="${line}${BG_YELLOW}${FG_CRUST}  ${branch}${star} ${RESET}"
  prev_fg="$FG_YELLOW"
fi

# model
line="${line}${prev_fg}${BG_GREEN}${ARROW}${RESET}"
line="${line}${BG_GREEN}${FG_CRUST} ${model} ${RESET}"
prev_fg="$FG_GREEN"

# context window usage
if [ -n "$ctx" ]; then
  ctx_rounded=$(printf '%.0f' "$ctx")
  line="${line}${prev_fg}${BG_SAPPHIRE}${ARROW}${RESET}"
  line="${line}${BG_SAPPHIRE}${FG_CRUST} ctx:${ctx_rounded}% ${RESET}"
  prev_fg="$FG_SAPPHIRE"
fi

# time
time_str=$(date '+%I:%M %p')
line="${line}${prev_fg}${BG_LAVENDER}${ARROW}${RESET}"
line="${line}${BG_LAVENDER}${FG_CRUST}  ${time_str} ${RESET}"
prev_fg="$FG_LAVENDER"

# 5-hour rate limit usage and time left
if [ -n "$five_h_pct" ]; then
  five_h_rounded=$(printf '%.0f' "$five_h_pct")
  reset_str=""
  if [ -n "$five_h_reset" ]; then
    now=$(date +%s)
    remaining=$((five_h_reset - now))
    [ "$remaining" -lt 0 ] && remaining=0
    rh=$((remaining / 3600))
    rm=$(((remaining % 3600) / 60))
    if [ "$rh" -gt 0 ]; then
      reset_str=" (${rh}h${rm}m left)"
    else
      reset_str=" (${rm}m left)"
    fi
  fi
  line="${line}${prev_fg}${BG_MAUVE}${ARROW}${RESET}"
  line="${line}${BG_MAUVE}${FG_CRUST} 5h:${five_h_rounded}%${reset_str} ${RESET}"
  prev_fg="$FG_MAUVE"
fi

# 7-day rate limit usage (compact, percentage only)
if [ -n "$seven_d_pct" ]; then
  seven_d_rounded=$(printf '%.0f' "$seven_d_pct")
  line="${line}${prev_fg}${BG_PINK}${ARROW}${RESET}"
  line="${line}${BG_PINK}${FG_CRUST} 7d:${seven_d_rounded}% ${RESET}"
  prev_fg="$FG_PINK"
fi

# rounded tail cap
line="${line}${prev_fg}${ROUND_RIGHT}${RESET}"

printf '%b\n' "$line"
