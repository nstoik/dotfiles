#!/usr/bin/env bash
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
  echo "Usage: pr-review.sh <PR_NUMBER>" >&2
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

DIFF_FILE=$(mktemp)
trap "rm -f '$DIFF_FILE'" EXIT
gh pr diff "$PR_NUMBER" > "$DIFF_FILE"

SECONDS=0
jq -n \
  --arg model "$OLLAMA_MODEL" \
  --rawfile system "$PROMPT_FILE" \
  --rawfile prompt "$DIFF_FILE" \
  --argjson stream false \
  '{model: $model, system: $system, prompt: $prompt, stream: $stream}' \
| curl -s -H 'Content-Type: application/json' "${OLLAMA_BASE_URL}/api/generate" --data @- \
| jq -r 'if .error then "Error: \(.error)" | halt_error(1) else .response end'
echo "" >&2
echo "Model: ${OLLAMA_MODEL}  Time: ${SECONDS}s" >&2
