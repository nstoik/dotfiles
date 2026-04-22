#!/usr/bin/env bash
set -euo pipefail

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:?OLLAMA_BASE_URL not set — export it in zshrc}"
OLLAMA_MODEL="${OLLAMA_MODEL:-deepseek-r1:8b}"

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

PROMPTS_DIR="${PROMPTS_DIR:-$HOME/ai/prompts}"
PROMPT_FILE="$PROMPTS_DIR/pr-review.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Error: prompt file not found: $PROMPT_FILE" >&2
  exit 1
fi

DIFF=$(gh pr diff "$1")
SYSTEM_PROMPT=$(cat "$PROMPT_FILE")

curl -s "${OLLAMA_BASE_URL}/api/generate" \
  -d "$(jq -n \
    --arg model "$OLLAMA_MODEL" \
    --arg system "$SYSTEM_PROMPT" \
    --arg prompt "$DIFF" \
    --argjson stream false \
    '{model: $model, system: $system, prompt: $prompt, stream: $stream}')" \
| jq -r '.response'
