---
type: automation-runbook
status: active
tags:
  - automation
  - cron
  - digitalocean
  - codex
  - ubuntu
---

# Ubuntu VPS Cron Setup

This runbook sets up a DigitalOcean Ubuntu VPS that runs the vault automation schedule.

The VPS owns:

- daily raw trend collection
- daily Codex Cloud task submission
- weekly raw trend preflight
- weekly Codex Cloud task submission

Codex Cloud owns:

- daily vault synthesis from `Machine/Automation/Prompts/daily-codex-cloud.md`
- weekly `/graphify`, markdown wiki refresh, and weekly vault synthesis from `Machine/Automation/Prompts/weekly-codex-cloud.md`

Graphify does not need to run daily. The VPS should not run shell Graphify with LLM keys. Weekly Graphify should run inside Codex Cloud through `/graphify`.

## Target Layout

```text
/home/<user_name>/codex-automations/
/home/<user_name>/codex-automations/.env
/home/<user_name>/codex-automations/logs/
/home/<user_name>/codex-automations/<REPO>/
```

## 1. Create SSH Key On Windows

Open Windows PowerShell.

Create the local SSH folder:

```powershell
mkdir $env:USERPROFILE\.ssh -Force
```

Create a key for the DigitalOcean VPS:

```powershell
ssh-keygen -t ed25519 -C "codex-cron-digitalocean" -f $env:USERPROFILE\.ssh\do_codex_cron
```

When it asks for a passphrase, press Enter if this VPS is only for cron automation.

Print the public key:

```powershell
Get-Content $env:USERPROFILE\.ssh\do_codex_cron.pub
```

Copy the full output. It starts with:

```text
ssh-ed25519 ...
```

## 2. Create DigitalOcean Droplet

In DigitalOcean:

```text
Create -> Droplets
Image: Ubuntu 24.04 LTS x64
Plan: Basic, cheapest shared CPU is enough
Region: Singapore if available
Authentication: SSH Key
Hostname: codex-cron
```

Paste the public key from PowerShell into the SSH key field.

After the Droplet is created, copy its public IP address.

## 3. SSH Into The VPS

From Windows PowerShell:

```powershell
ssh -i $env:USERPROFILE\.ssh\do_codex_cron root@YOUR_DROPLET_IP
```

Example:

```powershell
ssh -i $env:USERPROFILE\.ssh\do_codex_cron root@128.199.xxx.xxx
```

Type `yes` when SSH asks to trust the host.

## 4. Basic VPS Setup

Run these commands inside the VPS as `root`:

```bash
apt update
apt upgrade -y
apt install -y git curl ca-certificates cron ufw nano python3 python3-pip python3-venv
```

Create the normal user:

```bash
adduser <user_name>
usermod -aG sudo <user_name>
```

Copy SSH access from `root` to `<user_name>`:

```bash
mkdir -p /home/<user_name>/.ssh
cp /root/.ssh/authorized_keys /home/<user_name>/.ssh/authorized_keys
chown -R <user_name>:<user_name> /home/<user_name>/.ssh
chmod 700 /home/<user_name>/.ssh
chmod 600 /home/<user_name>/.ssh/authorized_keys
```

Exit root:

```bash
exit
```

Reconnect as the normal user from Windows PowerShell:

```powershell
ssh -i $env:USERPROFILE\.ssh\do_codex_cron <user_name>@YOUR_DROPLET_IP
```

## 5. Secure And Configure The VPS

Inside the VPS as `<user_name>`:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

Enable cron:

```bash
sudo systemctl enable --now cron
systemctl status cron
```

Set Vietnam timezone:

```bash
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
timedatectl
```

## 6. Create A GitHub SSH Key For The Private Repo

The Windows SSH key only gets you into the VPS. The VPS also needs its own GitHub key to clone and push the private repo.

Inside the VPS as `<user_name>`:

```bash
ssh-keygen -t ed25519 -C "codex-cron-vps-github" -f ~/.ssh/github_codex_cron
```

Press Enter for no passphrase.

Create or edit SSH config:

```bash
nano ~/.ssh/config
```

Paste:

```sshconfig
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_codex_cron
  IdentitiesOnly yes
```

Fix permissions:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/config ~/.ssh/github_codex_cron
chmod 644 ~/.ssh/github_codex_cron.pub
```

Print the public key:

```bash
cat ~/.ssh/github_codex_cron.pub
```

Add that key to GitHub.

Recommended path:

```text
GitHub -> <USER>/<REPO> -> Settings -> Deploy keys -> Add deploy key
Title: codex-cron-vps
Allow write access: enabled
```

Test GitHub SSH:

```bash
ssh -T git@github.com
```

Success looks like:

```text
Hi <USER>/<REPO>! You've successfully authenticated...
```

If you see `Permission denied (publickey)`, the deploy key is missing, copied wrong, or does not have access to the private repo.

## 7. Clone The Vault

Inside the VPS:

```bash
mkdir -p ~/codex-automations/logs
cd ~/codex-automations
git clone git@github.com:<USER>/<REPO>.git
cd <REPO>
```

Set Git identity for automated commits:

```bash
git config user.name "codex-cron"
git config user.email "codex-cron@users.noreply.github.com"
```

Test pull and push access:

```bash
git pull --ff-only origin main
git status
```

## 8. Create Python Environment

Install the repo Python dependencies:

```bash
cd ~/codex-automations/<REPO>
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r scripts/requirements-trending.txt
python -m pip install uv
python -m pip install graphifyy
```

Check Python:

```bash
which python
python --version
```

Expected Python path:

```text
/home/<user_name>/codex-automations/<REPO>/.venv/bin/python
```

## 9. Install And Login To Codex CLI

Install Codex CLI:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Add Codex to PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Check:

```bash
codex --version
```

Login:

```bash
codex login --device-auth
```

Open the displayed URL on your Windows browser, enter the code, and approve.

Check login:

```bash
codex login status
```

## 10. Codex Cloud Environment Setup

In the Codex Cloud environment settings for `<USER>/<REPO>`, configure:

```text
Agent internet access: On
Allowed HTTP methods: All methods
Additional allowed domains: comma-separated
```

Use comma-separated domains. Newline-separated domains may not be parsed correctly and can cause:

```text
CONNECT tunnel failed, response 403
```

Recommended domain allowlist:

```text
github.com, api.github.com, raw.githubusercontent.com, objects.githubusercontent.com, codeload.github.com, huggingface.co, cdn-lfs.huggingface.co, pypi.org, files.pythonhosted.org, npmjs.com, registry.npmjs.org, crates.io, hub.docker.com, arxiv.org, export.arxiv.org, paperswithcode.com, semanticscholar.org, api.semanticscholar.org, openreview.net, aclweb.org, aclanthology.org, proceedings.mlr.press, neurips.cc, icml.cc, iclr.cc, news.ycombinator.com, hn.algolia.com, reddit.com, old.reddit.com, youtube.com, www.youtube.com, youtubei.googleapis.com, googlevideo.com, api.search.brave.com, brave.com, generativelanguage.googleapis.com, api.scrapecreators.com, scrapecreators.com, app.scrapecreators.com, x.com, twitter.com, openai.com, platform.openai.com, anthropic.com, docs.anthropic.com, deepmind.google, ai.googleblog.com, ai.meta.com, mistral.ai, docs.mistral.ai, cohere.com, docs.cohere.com, nvidia.com, blogs.nvidia.com, microsoft.com, research.microsoft.com, microsoft.github.io, langchain.com, blog.langchain.com, docs.langchain.com, langchain-ai.github.io, langgraph.dev, llamaindex.ai, docs.llamaindex.ai, modelcontextprotocol.io, docs.cursor.com, docs.together.ai, docs.fireworks.ai, docs.perplexity.ai, the-decoder.com, venturebeat.com, techcrunch.com, simonwillison.net, latent.space, lilianweng.github.io, sebastianraschka.com, newsletter.pragmaticengineer.com, scholar.google.com
```

After changing environment settings, save the environment and reset the environment cache before submitting a new task.

Keep setup focused on dependencies only:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r scripts/requirements-trending.txt
python3 -m pip install uv
python3 -m pip install graphifyy
python3 -m pip install yt-dlp
npx -y @mvanhorn/printing-press-library@latest install digg --cli-only || true
```

Digg is optional. If the npm fetch fails, keep the `|| true` and continue; `last30days` still has Reddit, Hacker News, GitHub, Brave grounding, and YouTube.

Do not put runtime workflow commands in the Codex Cloud setup script.

Do not put these in setup:

```bash
python3 scripts/collect_github_trending.py || true
python3 scripts/collect_hf_hub_trends.py || true
graphify . --wiki || true
```

Reason:

- VPS cron runs collectors.
- Weekly Codex Cloud prompt runs `/graphify`.
- Environment setup should only prepare dependencies.

## 12.1 Codex Cloud Push Bootstrap

Codex Cloud task workspaces may start on an internal `work` branch with no `origin` remote. The daily and weekly wrapper scripts inject a short bootstrap prompt before the normal task prompt. It creates an authenticated `origin`, fetches `main`, and switches to `main`:

```bash
export OBSIDIAN_GITHUB_TOKEN='...'

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://x-access-token:${OBSIDIAN_GITHUB_TOKEN}@github.com/<USER>/<REPO>.git"
fi

git fetch origin main
git switch -C main origin/main
```

The actual scripts should read `OBSIDIAN_GITHUB_TOKEN` from `/home/<user_name>/codex-automations/.env`, not from the Codex Cloud environment secret store. This keeps the working setup under VPS control.

Expected script guards:

```bash
: "${CODEX_ENV_ID:?Set CODEX_ENV_ID in ~/codex-automations/.env}"
: "${OBSIDIAN_GITHUB_TOKEN:?Set OBSIDIAN_GITHUB_TOKEN in ~/codex-automations/.env}"
```

Safe checks inside Cloud:

```bash
git remote get-url origin >/dev/null && echo "origin configured"
git status --short --branch
git branch -vv
```

Unsafe checks after adding token remote:

```bash
git remote -v
git config --local --list
```

Do not run those in Cloud task logs.


## 11. Get Codex Cloud Environment ID

Run:

```bash
codex cloud
```

Find the environment for:

```text
<USER>/<REPO>
```

Copy the environment ID.

Known current environment ID:

```text
<YOUR_ENVIRONMENT_ID>
```

## 12. Configure Runtime Environment

Create the automation env file:

```bash
nano ~/codex-automations/.env
```

Paste:

```bash
HF_TOKEN=
OBSIDIAN_GITHUB_TOKEN=
PYTHON_BIN=/home/<user_name>/codex-automations/<REPO>/.venv/bin/python
PATH="/home/<user_name>/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
CODEX_ENV_ID=<YOUR_ENVIRONMENT_ID>
DEFAULT_BRANCH=main
VAULT_ROOT=/home/<user_name>/codex-automations/<REPO>

# last30days weekly discovery keys passed from this VPS env into the weekly
# Codex Cloud prompt by scripts/run_weekly_codex_cloud.sh. Do not add browser
# cookie variables such as AUTH_TOKEN or CT0 for Cloud automation.
SETUP_COMPLETE=true
GEMINI_API_KEY=
SCRAPECREATORS_API_KEY=
BRAVE_API_KEY=
GITHUB_TOKEN=
LAST30DAYS_REASONING_PROVIDER=gemini
LAST30DAYS_MEMORY_DIR=Machine/Last30Days
LAST30DAYS_DEFAULT_SEARCH=x,reddit,hackernews,github,grounding,youtube
EXCLUDE_SOURCES=tiktok,instagram,threads,linkedin,pinterest
INCLUDE_SOURCES=

# Optional Codex Cloud submit knobs.
# Leave model blank to use the environment/account default.
CODEX_DAILY_MODEL=
CODEX_DAILY_REASONING_EFFORT=medium
CODEX_DAILY_ATTEMPTS=1
CODEX_WEEKLY_MODEL=
CODEX_WEEKLY_REASONING_EFFORT=high
CODEX_WEEKLY_ATTEMPTS=1
```

`OBSIDIAN_GITHUB_TOKEN` is a fine-grained GitHub PAT used only by Codex Cloud tasks to add an authenticated HTTPS `origin` and push daily/weekly commits. Scope it to only `<USER>/<REPO>` with:

```text
Repository permissions:
- Contents: Read and write
- Metadata: Read-only
```

Do not print this token in logs. The Cloud task prompts and wrapper scripts should not run `git remote -v` or `git config --local --list` after adding the token remote, because those commands can expose the token.

`GITHUB_TOKEN` is used by `last30days` for GitHub API rate limits. It can be the same value as `OBSIDIAN_GITHUB_TOKEN` if the token is scoped only to this repository and you are comfortable reusing it for read-heavy GitHub API calls. If `GITHUB_TOKEN` is blank, `scripts/run_weekly_codex_cloud.sh` exports `OBSIDIAN_GITHUB_TOKEN` as `GITHUB_TOKEN` for the weekly Cloud task.

The default `last30days` weekly source set is intentionally conservative but includes X/Twitter when a server-friendly X backend key is configured:

```text
x,reddit,hackernews,github,grounding,youtube
```

For X/Twitter, set `XAI_API_KEY` or `XQUIK_API_KEY`. Do not use browser-cookie variables in Cloud. If both X keys are blank, the `x` source is simply unavailable and the weekly run should continue with the other sources.

Reddit uses public access and does not need a Reddit API key. `grounding` uses `BRAVE_API_KEY`. `youtube` uses `yt-dlp` first and can use ScrapeCreators as a fallback. TikTok, Instagram, Threads, LinkedIn, and Pinterest are excluded by default to avoid spending ScrapeCreators credits unless a weekly topic explicitly needs those channels.

Do not add these cookie-style X/Twitter variables to the VPS `.env` for Cloud automation:

```text
AUTH_TOKEN
CT0
TWITTER_AUTH_TOKEN
TWITTER_CT0
```

Secure it:

```bash
chmod 600 ~/codex-automations/.env
```

Load it for the current terminal:

```bash
set -a
. ~/codex-automations/.env
set +a
```

Check important values:

```bash
echo "$CODEX_ENV_ID"
echo "$PYTHON_BIN"
"$PYTHON_BIN" --version
```

## 13. Manual Test: Daily Collector

Inside the VPS:

```bash
cd ~/codex-automations/<REPO>
set -a
. ~/codex-automations/.env
set +a
bash scripts/run_daily_trend_collector.sh
```

Expected behavior:

- pulls latest `main`
- collects GitHub/Hugging Face trend inputs
- commits and pushes changes if files changed

Expected raw note paths:

```text
Inbox/GitHubTrending/YYYY/MM/DD.md
Inbox/HuggingFaceHub/YYYY/MM/DD.md
```

## 14. Manual Test: Daily Codex Cloud

Inside the VPS:

```bash
cd ~/codex-automations/<REPO>
set -a
. ~/codex-automations/.env
set +a
bash scripts/run_daily_codex_cloud.sh
```

Expected output:

```text
Submitting daily Codex Cloud automation...
https://chatgpt.com/codex/tasks/task_...
```

That means the VPS successfully submitted the daily prompt to Codex Cloud.

Inside the returned task URL, expected git behavior is:

```text
git fetch origin main
git switch -C main origin/main
git push origin HEAD:main
```

If `git fetch` or `git push` fails with:

```text
CONNECT tunnel failed, response 403
```

recheck the Codex Cloud domain allowlist. It must include `github.com`, and the domain list should be comma-separated.

The daily prompt file is:

```text
Machine/Automation/Prompts/daily-codex-cloud.md
```

## 15. Manual Test: Weekly Preflight

Inside the VPS:

```bash
cd ~/codex-automations/<REPO>
set -a
. ~/codex-automations/.env
set +a
bash scripts/run_weekly_codex_preflight.sh
```

Expected behavior:

- pulls latest `main`
- refreshes weekly trend inputs
- commits and pushes raw inputs if files changed
- does not run shell Graphify on the VPS

## 16. Manual Test: Weekly Codex Cloud

Inside the VPS:

```bash
cd ~/codex-automations/<REPO>
set -a
. ~/codex-automations/.env
set +a
bash scripts/run_weekly_codex_cloud.sh
```

Expected output:

```text
Submitting weekly Codex Cloud automation...
https://chatgpt.com/codex/tasks/task_...
```

The weekly prompt file is:

```text
Machine/Automation/Prompts/weekly-codex-cloud.md
```

The weekly Codex Cloud task should run `/graphify` before reading raw files, then verify `last30days` with:

```bash
python3 .agents/skills/last30days/scripts/last30days.py --diagnose --no-browser-cookies --emit json
```

Expected `last30days` sources with the conservative VPS `.env` are roughly:

```text
x, reddit, hackernews, github, grounding, youtube
```

If `XAI_API_KEY` and `XQUIK_API_KEY` are blank, `x` will be absent from diagnose output. That is acceptable; do not add `AUTH_TOKEN` or `CT0` to force X/Twitter in Cloud.

`tiktok`, `instagram`, `threads`, `linkedin`, and `pinterest` should stay off unless you deliberately remove them from `EXCLUDE_SOURCES` or pass a narrower explicit query that needs them.

## 16.1 Manual Test: Codex Cloud Push Smoke Test

Use this only after changing GitHub token, Codex Cloud environment domains, or Cloud push behavior.

The smoke-test task should:

- add authenticated `origin` using `OBSIDIAN_GITHUB_TOKEN`
- fetch `origin/main`
- create `Machine/Automation/Runbooks/codex-cloud-push-smoke-test.md`
- commit `Test Codex Cloud push`
- push to `main`

Success looks like:

```text
git fetch origin main
git switch -C main origin/main
git commit -m "Test Codex Cloud push"
git push origin HEAD:main
```

If the smoke test succeeds, the daily and weekly Cloud wrappers should be able to push too.

## 17. Install Crontab

Open crontab:

```bash
crontab -e
```

Paste:

```cron
SHELL=/bin/bash
CRON_TZ=Asia/Ho_Chi_Minh

# Daily raw trend collector. Pulls main first, then commits and pushes raw inputs.
0 22 * * * cd /home/<user_name>/codex-automations/<REPO> && set -a && . /home/<user_name>/codex-automations/.env && set +a && bash scripts/run_daily_trend_collector.sh >> /home/<user_name>/codex-automations/logs/daily-trends.log 2>&1

# Daily Codex Cloud automation. Uses Machine/Automation/Prompts/daily-codex-cloud.md.
0 8 * * * cd /home/<user_name>/codex-automations/<REPO> && set -a && . /home/<user_name>/codex-automations/.env && set +a && bash scripts/run_daily_codex_cloud.sh >> /home/<user_name>/codex-automations/logs/daily-codex.log 2>&1

# Sunday weekly input preflight. Pulls main first, then commits and pushes raw inputs.
30 7 * * 0 cd /home/<user_name>/codex-automations/<REPO> && set -a && . /home/<user_name>/codex-automations/.env && set +a && bash scripts/run_weekly_codex_preflight.sh >> /home/<user_name>/codex-automations/logs/weekly-preflight.log 2>&1

# Weekly Codex Cloud automation. Uses Machine/Automation/Prompts/weekly-codex-cloud.md and runs /graphify inside Codex Cloud.
0 8 * * 0 cd /home/<user_name>/codex-automations/<REPO> && set -a && . /home/<user_name>/codex-automations/.env && set +a && bash scripts/run_weekly_codex_cloud.sh >> /home/<user_name>/codex-automations/logs/weekly-codex.log 2>&1
```

Save and exit.

On Sundays, the daily and weekly Codex Cloud tasks both submit at 08:00. That is acceptable if the Cloud tasks can push cleanly, but if you see push races or non-fast-forward errors, move weekly Codex to `30 8 * * 0` or add a single shared `flock` around the Codex submit jobs.

Check installed cron jobs:

```bash
crontab -l
```

You are done when `crontab -l` shows the four jobs above.

## 18. Check Logs

Create logs folder if needed:

```bash
mkdir -p /home/<user_name>/codex-automations/logs
```

Check logs:

```bash
tail -n 120 /home/<user_name>/codex-automations/logs/daily-trends.log
tail -n 120 /home/<user_name>/codex-automations/logs/daily-codex.log
tail -n 120 /home/<user_name>/codex-automations/logs/weekly-preflight.log
tail -n 120 /home/<user_name>/codex-automations/logs/weekly-codex.log
```

Watch a log live:

```bash
tail -f /home/<user_name>/codex-automations/logs/daily-codex.log
```

Check cron service:

```bash
systemctl status cron
```

## 19. Current Automation Flow

```text
Daily:
  VPS cron
    -> git pull
    -> run_daily_trend_collector.sh
    -> commit/push raw trend inputs
    -> run_daily_codex_cloud.sh
    -> Codex Cloud uses daily-codex-cloud.md
    -> Codex Cloud commits/pushes daily synthesis

Weekly:
  VPS cron
    -> git pull
    -> run_weekly_codex_preflight.sh
    -> commit/push weekly raw inputs
    -> run_weekly_codex_cloud.sh
    -> Codex Cloud uses weekly-codex-cloud.md
    -> Codex Cloud runs /graphify
    -> Codex Cloud updates graph/wiki/retrieval outputs
    -> Codex Cloud commits/pushes weekly synthesis
```

## 20. Common Fixes

### `Permission denied (publickey)` for GitHub

Check:

```bash
ssh -T git@github.com
```

Fixes:

- add `~/.ssh/github_codex_cron.pub` to GitHub deploy keys
- enable write access on the deploy key
- confirm `~/.ssh/config` points `github.com` to `~/.ssh/github_codex_cron`
- confirm repo remote uses SSH:

```bash
git remote -v
```

Expected:

```text
git@github.com:<USER>/<REPO>.git
```

### `python3 -m venv .venv` fails

Install venv:

```bash
sudo apt update
sudo apt install -y python3-venv
```

Then recreate:

```bash
cd ~/codex-automations/<REPO>
python3 -m venv .venv
```

### `codex: command not found`

Reload PATH:

```bash
source ~/.bashrc
echo $PATH
which codex
```

Also confirm `.env` has:

```bash
PATH="/home/<user_name>/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

### Daily or weekly Codex task submits but does not commit

Open the task URL printed by:

```bash
bash scripts/run_daily_codex_cloud.sh
```

or:

```bash
bash scripts/run_weekly_codex_cloud.sh
```

The VPS only submits the Codex Cloud task. The task itself must finish successfully and push changes.

Expected Cloud git setup:

```bash
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://x-access-token:${OBSIDIAN_GITHUB_TOKEN}@github.com/<USER>/<REPO>.git"
git fetch origin main
git switch -C main origin/main
```

If Cloud reports:

```text
error: No such remote 'origin'
```

then the token bootstrap did not run or `OBSIDIAN_GITHUB_TOKEN` was not injected by the VPS wrapper.

If Cloud reports:

```text
CONNECT tunnel failed, response 403
```

then the Codex Cloud internet allowlist is blocking the network request. Confirm:

- `github.com` is included
- domains are comma-separated
- the environment was saved
- the environment cache was reset
- the task was submitted after the change

If Cloud reports an authentication or permission error after connecting to GitHub, check the fine-grained PAT:

- selected repo is `<USER>/<REPO>`
- `Contents` is `Read and write`
- token is not expired
- `/home/<user_name>/codex-automations/.env` has `OBSIDIAN_GITHUB_TOKEN=...`

### Graphify asks for `GEMINI_API_KEY` or `OPENAI_API_KEY`

You are probably running shell Graphify directly on the VPS.

Desired setup:

- do not run `graphify . --wiki` in VPS cron
- do not run `graphify . --wiki` in Codex Cloud setup
- run `/graphify` inside the weekly Codex Cloud task

### Cron works manually but not on schedule

Check:

```bash
crontab -l
systemctl status cron
tail -n 120 /home/<user_name>/codex-automations/logs/daily-codex.log
```

Most cron failures are PATH or missing env values. Keep absolute paths in crontab and source `/home/<user_name>/codex-automations/.env`.

### Repo has merge conflicts or pull fails

Go to the repo:

```bash
cd /home/<user_name>/codex-automations/<REPO>
git status
```

Do not blindly reset. Check what changed, then resolve conflicts or ask Codex to inspect the repo.
