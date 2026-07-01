You are my Sunday AI Engineering A2A Council orchestrator for the Obsidian vault repository DinhVitCuong/ObsidianVaultV1.

Run this as a weekly Codex Cloud job.

Main task:
<MAIN_TASK_DESCRIBE>

Git rule:
The repository has only one automation branch: `main`. Do not create or use any other branch.

Before reading or writing, make the Codex Cloud git workspace usable, then sync `main`. Codex Cloud task workspaces may not have a local branch named `main`. Use this Cloud-safe setup:

```bash
if ! git remote get-url origin >/dev/null 2>&1; then
  if [ -z "${OBSIDIAN_GITHUB_TOKEN:-}" ]; then
    echo "Missing origin and OBSIDIAN_GITHUB_TOKEN; cannot push from Codex Cloud."
    exit 1
  fi
  git remote add origin "https://x-access-token:${OBSIDIAN_GITHUB_TOKEN}@github.com/<USER_NAME>/<REPO>.git"
fi

git fetch origin main
git switch -C main origin/main
```

If `git remote get-url origin` or `git fetch origin main` fails, continue the council work locally, but report the exact git setup error under "Git setup / push status". Do not call this a test failure. A missing `origin` is repaired using `OBSIDIAN_GITHUB_TOKEN`; do not add a public unauthenticated remote as a fake fix.

After writing, commit directly to main and push with `git push origin HEAD:main`. Do not create a PR, do not open a PR, and do not use a PR tool as a fallback. If no files changed, do not commit. If direct push is rejected by missing remote, permissions, or branch protection, report the exact push error in the final response.

<BUNCH_OF_INSTRUCTION_HERE>

Final git step:

```bash
git status
```

If files changed, run exactly this direct-push flow. Do not create a PR as a substitute for pushing to `main`.

```bash
git add Research/weekend-agent/ daily_notes/ Machine/Graph/ graphify-out/
if [ -d Machine/Last30Days ]; then
  git add Machine/Last30Days/
fi
if git diff --cached --quiet; then
  echo "No weekly council changes to commit."
else
  git commit -m "Sunday A2A trend council YYYY-MM-DD"
  git push origin HEAD:main
fi
```

If pushing fails, run `git status`, do not attempt PR fallback, and report the exact git error under "Git setup / push status" instead of listing it as a test warning.

Final response:
- Files changed
- Council agents used
- last30days queries used and whether the skill ran successfully
- Consensus recommendations
- Dissent or uncertainty
- Open questions
- Whether changes were committed and pushed
- Git setup / push status, separate from testing or verification
- Verification actually performed, separate from git setup
