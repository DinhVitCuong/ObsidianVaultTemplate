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

PROMPT=$(cat <<EOF
You are testing whether Codex Cloud can commit and push to DinhVitCuong/ObsidianVaultV1.

Do not print secrets. Do not run git remote -v. Do not run git config --local --list.

First configure GitHub origin:

\`\`\`bash
export OBSIDIAN_GITHUB_TOKEN='${OBSIDIAN_GITHUB_TOKEN}'

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://x-access-token:\${OBSIDIAN_GITHUB_TOKEN}@github.com/DinhVitCuong/ObsidianVaultV1.git"
fi

git fetch origin main
git switch -C main origin/main
\`\`\`

Then create a tiny smoke-test commit:

\`\`\`bash
mkdir -p Machine/Automation/Runbooks
{
  echo "# Codex Cloud Push Smoke Test"
  echo
  echo "- Ran at: \$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- Purpose: verify Codex Cloud can commit and push to main."
} > Machine/Automation/Runbooks/codex-cloud-push-smoke-test.md

git add Machine/Automation/Runbooks/codex-cloud-push-smoke-test.md
git commit -m "Test Codex Cloud push"
git push origin HEAD:main
git status --short --branch
\`\`\`

Final response:
- Whether commit succeeded
- Whether push succeeded
- Commit hash
- Any exact error
EOF
)

echo "Submitting Codex Cloud push smoke test..."
codex cloud exec --env "${CODEX_ENV_ID}" --branch "${MAIN_BRANCH}" "${PROMPT}"
