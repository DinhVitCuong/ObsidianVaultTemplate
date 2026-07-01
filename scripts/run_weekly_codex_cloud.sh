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
PROMPT_FILE="${CODEX_WEEKLY_PROMPT_FILE:-Machine/Automation/Prompts/weekly-codex-cloud.md}"

if ! command -v codex >/dev/null 2>&1; then
  echo "Missing codex CLI. Install or load Codex before submitting the weekly Cloud job." >&2
  exit 1
fi

if [ ! -s "${PROMPT_FILE}" ]; then
  echo "Missing weekly Codex Cloud prompt file: ${PROMPT_FILE}" >&2
  exit 1
fi

PROMPT="$(cat "${PROMPT_FILE}")"

CLOUD_ENV_KEYS="${LAST30DAYS_CLOUD_ENV_KEYS:-SETUP_COMPLETE GEMINI_API_KEY GOOGLE_API_KEY GOOGLE_GENAI_API_KEY SCRAPECREATORS_API_KEY SCRAPE_CREATORS_API_KEY XAI_API_KEY XQUIK_API_KEY BRAVE_API_KEY EXA_API_KEY SERPER_API_KEY PARALLEL_API_KEY PERPLEXITY_API_KEY OPENROUTER_API_KEY GITHUB_TOKEN GROQ_API_KEY BSKY_HANDLE BSKY_APP_PASSWORD INCLUDE_SOURCES EXCLUDE_SOURCES LAST30DAYS_MEMORY_DIR LAST30DAYS_REASONING_PROVIDER LAST30DAYS_PLANNER_MODEL LAST30DAYS_RERANK_MODEL LAST30DAYS_DEFAULT_SEARCH LAST30DAYS_NATIVE_SEARCH}"

CLOUD_ENV_EXPORTS=""
append_cloud_env_export() {
  local key="$1"
  local value="${!key-}"
  local quoted=""

  case "${key}" in
    AUTH_TOKEN|CT0|TWITTER_AUTH_TOKEN|TWITTER_CT0)
      return 0
      ;;
  esac

  if [ -n "${value}" ]; then
    printf -v quoted "%q" "${value}"
    CLOUD_ENV_EXPORTS+="export ${key}=${quoted}"$'\n'
  fi
}

for key in ${CLOUD_ENV_KEYS}; do
  append_cloud_env_export "${key}"
done

if [ -z "${GITHUB_TOKEN:-}" ] && [ -n "${OBSIDIAN_GITHUB_TOKEN:-}" ]; then
  printf -v _github_token_quoted "%q" "${OBSIDIAN_GITHUB_TOKEN}"
  CLOUD_ENV_EXPORTS+="export GITHUB_TOKEN=${_github_token_quoted}"$'\n'
fi

if [ -z "${SETUP_COMPLETE:-}" ]; then
  CLOUD_ENV_EXPORTS+="export SETUP_COMPLETE=true"$'\n'
fi

if [ -z "${LAST30DAYS_MEMORY_DIR:-}" ]; then
  CLOUD_ENV_EXPORTS+="export LAST30DAYS_MEMORY_DIR=Machine/Last30Days"$'\n'
fi

if [ -z "${LAST30DAYS_DEFAULT_SEARCH:-}" ]; then
  CLOUD_ENV_EXPORTS+="export LAST30DAYS_DEFAULT_SEARCH=x,reddit,hackernews,github,grounding,youtube"$'\n'
fi

if [ -z "${EXCLUDE_SOURCES:-}" ]; then
  CLOUD_ENV_EXPORTS+="export EXCLUDE_SOURCES=tiktok,instagram,threads,linkedin,pinterest"$'\n'
fi

GIT_BOOTSTRAP=$(cat <<EOF
Cloud GitHub token bootstrap:
Before any git fetch, commit, or push, run this setup. Do not print the token, do not run git remote -v, and do not run git config --local --list.

\`\`\`bash
export OBSIDIAN_GITHUB_TOKEN='${OBSIDIAN_GITHUB_TOKEN}'
${CLOUD_ENV_EXPORTS}

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://x-access-token:\${OBSIDIAN_GITHUB_TOKEN}@github.com/<USER>/<REPO>.git"
fi

git fetch origin main
git switch -C main origin/main
\`\`\`

EOF
)

echo "Submitting weekly Codex Cloud automation..."
codex cloud exec --env "${CODEX_ENV_ID}" --branch "${MAIN_BRANCH}" "${GIT_BOOTSTRAP}${PROMPT}"
