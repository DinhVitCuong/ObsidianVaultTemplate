#!/usr/bin/env bash
set -euo pipefail

if [ -n "${VAULT_ROOT:-}" ]; then
  cd "${VAULT_ROOT}"
else
  cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

echo "Syncing ${DEFAULT_BRANCH} before daily trend collection..."
git fetch origin "${DEFAULT_BRANCH}"
git checkout "${DEFAULT_BRANCH}"
git pull --ff-only origin "${DEFAULT_BRANCH}"

PYTHON_BIN="${PYTHON_BIN:-/home/<user_name>/codex-automations/<REPO>/.venv/bin/python}"
export PYTHON_BIN

echo "Collecting daily trend inputs..."
"${PYTHON_BIN}" scripts/collect_github_trending.py
"${PYTHON_BIN}" scripts/collect_hf_hub_trends.py

echo "Committing daily trend outputs..."
git config user.name >/dev/null 2>&1 || git config user.name "codex-cron"
git config user.email >/dev/null 2>&1 || git config user.email "codex-cron@users.noreply.github.com"

git add Inbox/GitHubTrending/ Inbox/HuggingFaceHub/

if git diff --cached --quiet; then
  echo "No daily trend changes to commit."
else
  git commit -m "Collect AI trend signals"
fi

git push origin "${DEFAULT_BRANCH}"
