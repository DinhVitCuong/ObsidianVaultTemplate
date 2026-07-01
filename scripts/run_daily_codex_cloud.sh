#!/usr/bin/env bash
set -euo pipefail

: "${CODEX_ENV_ID:?Set CODEX_ENV_ID in ~/codex-automations/.env}"
: "${OBSIDIAN_GITHUB_TOKEN:?Set OBSIDIAN_GITHUB_TOKEN in ~/codex-automations/.env}"

if [ -n "${VAULT_ROOT:-}" ]; then
  cd "${VAULT_ROOT}"
else
  cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

MAIN_BRANCH="main"
PROMPT_FILE="${CODEX_DAILY_PROMPT_FILE:-Machine/Automation/Prompts/daily-codex-cloud.md}"

if ! command -v codex >/dev/null 2>&1; then
  echo "Missing codex CLI. Install or load Codex before submitting the daily Cloud job." >&2
  exit 1
fi

if [ ! -s "${PROMPT_FILE}" ]; then
  echo "Missing daily Codex Cloud prompt file: ${PROMPT_FILE}" >&2
  exit 1
fi

PROMPT="$(cat "${PROMPT_FILE}")"

GIT_BOOTSTRAP=$(cat <<EOF
Cloud GitHub token bootstrap:
Before any git fetch, commit, or push, run this setup. Do not print the token, do not run git remote -v, and do not run git config --local --list.

\`\`\`bash
export OBSIDIAN_GITHUB_TOKEN='${OBSIDIAN_GITHUB_TOKEN}'

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://x-access-token:\${OBSIDIAN_GITHUB_TOKEN}@github.com/<USER>/<REPO>.git"
fi

git fetch origin main
git switch -C main origin/main
\`\`\`

EOF
)

echo "Submitting daily Codex Cloud automation..."
codex cloud exec --env "${CODEX_ENV_ID}" --branch "${MAIN_BRANCH}" "${GIT_BOOTSTRAP}${PROMPT}"
