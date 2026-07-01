#!/usr/bin/env bash
set -euo pipefail

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:?OLLAMA_BASE_URL not set — export it in zshrc}"
MODELS_FILE="${MODELS_FILE:-$HOME/ai/models.txt}"

if ! command -v curl &>/dev/null; then
  echo "Error: curl is required but not installed." >&2
  exit 1
fi
if ! command -v jq &>/dev/null; then
  echo "Error: jq is required but not installed. Install with: sudo apt install jq" >&2
  exit 1
fi

if [[ ! -f "$MODELS_FILE" ]]; then
  echo "Error: models file not found: $MODELS_FILE" >&2
  exit 1
fi

# Read desired models (strip comments and blank lines)
mapfile -t DESIRED < <(grep -v '^\s*#' "$MODELS_FILE" | grep -v '^\s*$')

if [[ ${#DESIRED[@]} -eq 0 ]]; then
  echo "No models listed in $MODELS_FILE — nothing to do." >&2
  exit 0
fi

echo "==> Pulling ${#DESIRED[@]} model(s)..."
for model in "${DESIRED[@]}"; do
  echo "--- $model"
  curl -s "${OLLAMA_BASE_URL}/api/pull" \
    -d "$(jq -n --arg model "$model" --argjson stream false '{model: $model, stream: $stream}')" \
  | jq -r '.status'
done

echo ""
echo "==> Removing unlisted models..."
INSTALLED=$(curl -s "${OLLAMA_BASE_URL}/api/tags" | jq -r '.models[].name')

removed=0
while IFS= read -r installed_model; do
  if printf '%s\n' "${DESIRED[@]}" | grep -qxF "$installed_model"; then
    continue
  fi
  echo "--- removing $installed_model"
  curl -s -X DELETE "${OLLAMA_BASE_URL}/api/delete" \
    -d "$(jq -n --arg model "$installed_model" '{model: $model}')" > /dev/null
  ((removed++)) || true
done <<< "$INSTALLED"

if [[ $removed -eq 0 ]]; then
  echo "No unlisted models to remove."
fi

echo ""
echo "Done."
