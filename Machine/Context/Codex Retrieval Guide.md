---
type: codex-context
status: active
tags:
  - codex
  - retrieval
  - graph
---

# Codex Retrieval Guide

Use this file as the first stop before reading large parts of the vault.

## Fast Path

1. Read [[Machine/Graph/retrieval-map|Retrieval Map]].
2. Read [[Machine/Graph/GRAPH_REPORT|Graph Report]].
3. For weekly flows, read [[Machine/Graph/codex-weekly-wiki|Codex Weekly Wiki]] before raw trend notes.
4. Check [[Dashboard]] for the current operating view.
5. Open only the files named by the retrieval map, graph report, or weekly wiki.

## Canonical Daily Notes

Daily notes live at:

```text
daily_notes/YYYY/MM/DD.md
```

Do not create or update `Daily/YYYY-MM-DD.md` or `daily_notes/YYYY-MM-DD.md`.

## Automation Inputs

All Inbox raw notes use nested date paths: `Inbox/<Source>/YYYY/MM/DD.md`.

- ChatGPT captures: `Inbox/ChatGPT/`
- Codex captures: `Inbox/Codex/`
- Code/git captures: `Inbox/Code/`
- GitHub trend captures: `Inbox/GitHubTrending/`
- Hugging Face trend captures: `Inbox/HuggingFaceHub/`
- Daily notes: `daily_notes/`

## Automation Outputs

- Daily agent notes: `Research/daily-agent/YYYY/MM/DD.md`
- Weekly trend research: `Research/weekend-agent/YYYY/MM/DD.md`
- Graph outputs: `Machine/Graph/`
- Weekly Codex markdown feed: `Machine/Graph/codex-weekly-wiki.md`
- Graphify raw outputs, if produced by the Graphify CLI: `graphify-out/`
- Automation prompts: `Machine/Automation/Prompts/`
- Automation runbooks: `Machine/Automation/Runbooks/`

## Graphify Setup

Preferred weekly flow: run Graphify from inside Codex with `/graphify`, not from the Ubuntu VPS shell. This avoids storing LLM provider API keys on the VPS.

```bash
python -m pip install uv
uv tool install graphifyy --force
export PATH="$HOME/.local/bin:$PATH"
graphify --help
```

The local wrapper remains available as a fallback for manual shell usage:

```bash
bash scripts/update_graphify_index.sh
```

For the Sunday weekly Codex flow on an Ubuntu VPS crontab runner, run the full preflight before feeding Codex:

```bash
bash scripts/run_weekly_codex_preflight.sh
```

The preflight pulls `main` first, then commits and pushes refreshed feed outputs to `main` by default.

## Update Safety

- Never overwrite `## Start of day`.
- Update only `## End of day` in daily notes.
- Keep raw capture notes intact.
- Prefer summary links to copying long raw excerpts.
