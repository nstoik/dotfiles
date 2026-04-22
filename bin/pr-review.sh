#!/usr/bin/env bash
set -euo pipefail

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://172.22.208.1:11434}"

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

DIFF=$(gh pr diff "$1")
SYSTEM_PROMPT="You are a senior developer doing a code review. Review this PR diff for: security issues, bugs, code quality, and anything suspicious or wrong. Be concise and specific."

curl -s "${OLLAMA_BASE_URL}/api/generate" \
  -d "$(jq -n \
    --arg model "deepseek-r1:8b" \
    --arg system "$SYSTEM_PROMPT" \
    --arg prompt "$DIFF" \
    --argjson stream false \
    '{model: $model, system: $system, prompt: $prompt, stream: $stream}')" \
| jq -r '.response'
