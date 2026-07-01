#!/usr/bin/env bash
set -euo pipefail

if [ -n "${VAULT_ROOT:-}" ]; then
  cd "${VAULT_ROOT}"
else
  cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Syncing ${DEFAULT_BRANCH} before weekly preflight..."
  git fetch origin "${DEFAULT_BRANCH}"
  git checkout "${DEFAULT_BRANCH}"
  git pull --ff-only origin "${DEFAULT_BRANCH}"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi
export PYTHON_BIN

echo "Collecting weekly trend inputs..."
"${PYTHON_BIN}" scripts/collect_github_trending.py || true
"${PYTHON_BIN}" scripts/collect_hf_hub_trends.py || true

if [ "${PREFLIGHT_COMMIT:-1}" = "1" ]; then
  echo "Committing weekly input outputs..."
  git config user.name >/dev/null 2>&1 || git config user.name "codex-cron"
  git config user.email >/dev/null 2>&1 || git config user.email "codex-cron@users.noreply.github.com"

  git add Inbox/GitHubTrending/ Inbox/HuggingFaceHub/

  if git diff --cached --quiet; then
    echo "No weekly input changes to commit."
  else
    git commit -m "Collect weekly AI trend inputs"
  fi

  if [ "${PREFLIGHT_PUSH:-1}" = "1" ]; then
    git push origin "${DEFAULT_BRANCH}"
  fi
fi

echo "Weekly Codex input preflight ready. Trigger Codex Cloud next so Codex can run /graphify and write the weekly note."
