#!/bin/sh
# Claude Code status line — powerline style mirroring the starship prompt
# (catppuccin-mocha palette): user@host | dir | git | model | ctx% | time
input=$(cat)

# Single jq call extracting every field via TSV, instead of one echo|jq fork per field
tsv=$(printf '%s' "$input" | jq -r '[
  .workspace.current_dir,
  .model.display_name,
  (.context_window.used_percentage // ""),
  (.rate_limits.five_hour.used_percentage // ""),
  (.rate_limits.five_hour.resets_at // ""),
  (.rate_limits.seven_day.used_percentage // "")
] | join("\u001f")')
oldifs="$IFS"
IFS=$(printf '\037')
set -f
set -- $tsv
set +f
IFS="$oldifs"
dir=$1
model=$2
ctx=$3
five_h_pct=$4
five_h_reset=$5
seven_d_pct=$6

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

# Appends one powerline segment to $line: an arrow fading from the previous
# segment's color into $1 (this segment's bg), then $1's block containing $2.
# Updates $prev_fg to $3 so the next segment's arrow fades from this one.
seg() {
  line="${line}${prev_fg}${1}${ARROW}${RESET}${1}${FG_CRUST} ${2} ${RESET}"
  prev_fg="$3"
}

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
  if ($1 == "") n = n - 1
  if (n <= 3) { print; next }
  out = "\xe2\x80\xa6"
  for (i = NF - 2; i <= NF; i++) out = out "/" $i
  print out
}')

# rounded head cap
line="${FG_RED}${ROUND_LEFT}${RESET}"

# user@host (host only shown over SSH, matching the starship hostname behavior)
line="${line}${BG_RED}${FG_CRUST}  ${user}"
if [ -n "$SSH_TTY" ] || [ -n "$SSH_CONNECTION" ]; then
  line="${line}@${host}"
fi
line="${line} ${RESET}"
prev_fg="$FG_RED"

# directory
seg "$BG_PEACH" "$trunc_dir" "$FG_PEACH"

# git branch and dirty status (skip optional locks). symbolic-ref/rev-parse
# already fail outside a repo, so no separate rev-parse --git-dir probe is needed.
if branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null || git -C "$dir" rev-parse --short HEAD 2>/dev/null) && [ -n "$branch" ]; then
  dirty=$(git --no-optional-locks -C "$dir" status --porcelain 2>/dev/null | head -1)
  if [ -n "$dirty" ]; then
    star=" *"
  else
    star=""
  fi
  seg "$BG_YELLOW" " ${branch}${star}" "$FG_YELLOW"
fi

# model
seg "$BG_GREEN" "$model" "$FG_GREEN"

# context window usage
if [ -n "$ctx" ]; then
  ctx_rounded=$(printf '%.0f' "$ctx")
  seg "$BG_SAPPHIRE" "ctx:${ctx_rounded}%" "$FG_SAPPHIRE"
fi

# time (also captures epoch seconds in the same `date` call, for the 5h countdown below)
date_out=$(date '+%I:%M %p|%s')
time_str="${date_out%|*}"
now="${date_out#*|}"
seg "$BG_LAVENDER" " ${time_str}" "$FG_LAVENDER"

# 5-hour rate limit usage and time left
if [ -n "$five_h_pct" ]; then
  five_h_rounded=$(printf '%.0f' "$five_h_pct")
  reset_str=""
  if [ -n "$five_h_reset" ]; then
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
  seg "$BG_MAUVE" "5h:${five_h_rounded}%${reset_str}" "$FG_MAUVE"
fi

# 7-day rate limit usage (compact, percentage only)
if [ -n "$seven_d_pct" ]; then
  seven_d_rounded=$(printf '%.0f' "$seven_d_pct")
  seg "$BG_PINK" "7d:${seven_d_rounded}%" "$FG_PINK"
fi

# rounded tail cap
line="${line}${prev_fg}${ROUND_RIGHT}${RESET}"

printf '%b\n' "$line"
