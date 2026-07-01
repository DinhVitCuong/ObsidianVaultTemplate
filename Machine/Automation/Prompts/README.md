---
type: automation-prompts-index
status: active
tags:
  - automation
  - codex
---

# Automation Prompts

This folder is the canonical home for automation prompts.

The real Codex Cloud jobs use `daily-codex-cloud.md` and `weekly-codex-cloud.md`. `Cloud Automation Prompts.md` is a reference/template note for humans.

- [[Machine/Automation/Prompts/Cloud Automation Prompts|Cloud Automation Prompts]]
- [[Machine/Automation/Prompts/daily-codex-cloud|Daily Codex Cloud Prompt]]
- [[Machine/Automation/Prompts/weekly-codex-cloud|Weekly Codex Cloud Prompt]]
- [[Machine/Automation/Runbooks/Ubuntu VPS Cron Setup|Ubuntu VPS Cron Setup]]
- [[Sources/ai_trend_source_allowlist|AI Trend Source Allowlist]]

Daily jobs should not refresh Graphify. Weekly jobs refresh Graphify and the markdown wiki feed before the Sunday Codex flow.

When jobs are submitted by VPS crontab, edit model/effort/attempt submit settings through `~/codex-automations/.env`. The wrapper scripts read `CODEX_DAILY_MODEL`, `CODEX_DAILY_REASONING_EFFORT`, `CODEX_DAILY_ATTEMPTS`, `CODEX_WEEKLY_MODEL`, `CODEX_WEEKLY_REASONING_EFFORT`, and `CODEX_WEEKLY_ATTEMPTS`.

Edit source/domain permissions in `Sources/ai_trend_source_allowlist.md`. Edit topic intent in `Sources/github_trending_targets.md` and `Sources/hf_hub_targets.md`. Edit runnable Codex job behavior in `daily-codex-cloud.md` and `weekly-codex-cloud.md`.
