#!/usr/bin/env bash
# pr-review.sh - Review a GitHub pull request using a local Ollama model
#
# Usage: pr-review.sh <PR_NUMBER> [-- ':!<glob>' ...]
#
# Arguments:
#   PR_NUMBER      GitHub pull request number
#   -- ':!<glob>'  Exclude files matching glob from the diff (repeatable)
#                  Examples: ':!*.json'  ':!package-lock.json'
#
# Environment variables:
#   OLLAMA_BASE_URL  Base URL of the Ollama API (required)
#   OLLAMA_MODEL     Model to use (default: qwen2.5-coder:14b)
#   PROMPTS_DIR      Directory containing pr-review.md prompt (default: ~/ai/prompts)
set -euo pipefail

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:?OLLAMA_BASE_URL not set — export it in zshrc}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5-coder:14b}"

if ! command -v jq &>/dev/null; then
  echo "Error: jq is required but not installed. Install with: sudo apt install jq" >&2
  exit 1
fi
if ! command -v gh &>/dev/null; then
  echo "Error: gh (GitHub CLI) is required but not installed. See https://cli.github.com" >&2
  exit 1
fi

if [[ -z "${1:-}" ]]; then
  echo "Usage: pr-review.sh <PR_NUMBER> [-- ':!<glob>' ...]" >&2
  exit 1
fi

PR_NUMBER="$1"
shift

PROMPTS_DIR="${PROMPTS_DIR:-$HOME/ai/prompts}"
PROMPT_FILE="$PROMPTS_DIR/pr-review.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Error: prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

# Parse ':!glob' exclusion args into filterdiff --exclude flags
EXCLUDE_ARGS=()
for arg in "$@"; do
  if [[ "$arg" == ":!"* ]]; then
    EXCLUDE_ARGS+=("--exclude=${arg#:!}")
  fi
done

DIFF_FILE=$(mktemp)
RESPONSE_FILE=$(mktemp)
trap 'rm -f "$DIFF_FILE" "$RESPONSE_FILE"' EXIT

if [[ ${#EXCLUDE_ARGS[@]} -gt 0 ]]; then
  if ! command -v filterdiff &>/dev/null; then
    echo "Error: filterdiff is required for file exclusion. Install with: sudo apt install patchutils" >&2
    exit 1
  fi
  gh pr diff "$PR_NUMBER" | filterdiff "${EXCLUDE_ARGS[@]}"
else
  gh pr diff "$PR_NUMBER"
fi > "$DIFF_FILE"

SECONDS=0
jq -n \
  --arg model "$OLLAMA_MODEL" \
  --rawfile system "$PROMPT_FILE" \
  --rawfile prompt "$DIFF_FILE" \
  --argjson stream false \
  '{model: $model, system: $system, prompt: $prompt, stream: $stream}' \
| curl -s -H 'Content-Type: application/json' "${OLLAMA_BASE_URL}/api/generate" --data @- \
> "$RESPONSE_FILE" &
CURL_PID=$!

SPIN_PREFIX="Reviewing PR #${PR_NUMBER} with ${OLLAMA_MODEL}"
SPINSTR='|/-\'
while kill -0 "$CURL_PID" 2>/dev/null; do
  printf "\r%s %s" "$SPIN_PREFIX" "${SPINSTR:0:1}" >&2
  SPINSTR="${SPINSTR:1}${SPINSTR:0:1}"
  sleep 0.2
done
wait "$CURL_PID"
printf "\r\033[K" >&2

jq -r 'if .error then "Error: \(.error)" | halt_error(1) else .response end' "$RESPONSE_FILE"
echo "" >&2
echo "Model: ${OLLAMA_MODEL}  Time: ${SECONDS}s" >&2
