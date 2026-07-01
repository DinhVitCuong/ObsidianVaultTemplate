# ObsidianVaultV1 Agent Guide

This repository is an Obsidian vault for AI engineering learning, daily review, trend collection, and Codex-assisted retrieval.

## Canonical Paths

- Dashboard: `Dashboard.md`
- Daily notes: `daily_notes/YYYY/MM/DD.md`
- Daily note template: `Template/Daily.md`
- Raw ChatGPT captures: `Inbox/ChatGPT/`
- Raw Codex captures: `Inbox/Codex/`
- Raw code/git captures: `Inbox/Code/`
- GitHub trend raw notes: `Inbox/GitHubTrending/`
- Hugging Face trend raw notes: `Inbox/HuggingFaceHub/`
- Daily agent research notes: `Research/daily-agent/YYYY/MM/DD.md`
- Weekend agent research notes: `Research/weekend-agent/YYYY/MM/DD.md`
- Other synthesized research notes: `Research/`
- Graph/retrieval outputs: `Machine/Graph/`
- Weekly Codex markdown feed: `Machine/Graph/codex-weekly-wiki.md`
- Automation prompts: `Machine/Automation/Prompts/`
- Automation runbooks: `Machine/Automation/Runbooks/`
- Codex context notes: `Machine/Context/`

## Daily Note Rules

- Daily notes use the nested path `daily_notes/YYYY/MM/DD.md`.
- Inbox raw notes use the nested path `Inbox/<Source>/YYYY/MM/DD.md`.
- Never overwrite `## Start of day`.
- If updating a daily note, update only `## End of day`.
- Preserve handwritten notes and raw observations.
- Keep summaries concise and practical.

## Retrieval Rules

Before reading many raw notes, check:

1. `Machine/Context/Codex Retrieval Guide.md`
2. `Machine/Graph/retrieval-map.md`
3. `Machine/Graph/GRAPH_REPORT.md`
4. `Dashboard.md`
5. Source target files under `Sources/`

Only open raw trend notes after the graph/retrieval files point to relevant files.

## Trend Research Rules

- X/Twitter is allowed for discovery only.
- Verify X/Twitter/community claims through primary sources before treating them as trends: repos, papers, model cards, docs, release notes, official blogs, or runnable demos.
- Do not delete raw notes.
- Prefer actionable engineering insight over hype.
- For daily runs, include only 1-3 high-signal trend items.
- For weekly runs, separate try-now, watch-later, and ignore items.

## Graphify Contract

Codex-side `/graphify` is the preferred graph builder for weekly automation. The VPS should prepare raw inputs and trigger Codex; Codex should run `/graphify` before reading raw files.

The local wrapper remains available as a fallback and will:

1. Expect Graphify to be installed once on the VPS, usually with `uv tool install graphifyy --force`.
2. Run `graphify . --wiki` or `graphify . --update --wiki` when the `graphify` command exists.
3. Build stable Codex retrieval outputs under `Machine/Graph/` every time.
4. Build `Machine/Graph/codex-weekly-wiki.md` for the Sunday Codex weekly flow.

Graphify does not run as part of daily raw trend collection. The VPS weekly preflight should not run shell Graphify. Run `/graphify` inside the weekly Codex Cloud task.

Automation git policy:

- Every VPS automation pulls `main` before doing work.
- Every daily and weekly automation commits directly to `main` and pushes.
- Do not create PRs for daily or weekly automation outputs unless the user explicitly asks.

Run the full wrapper with:

```bash
bash scripts/update_graphify_index.sh
```

Run only the local Codex retrieval normalizer with:

```bash
python scripts/build_graphify_index.py
```

Run the full Ubuntu VPS weekly preflight before feeding the Sunday Codex flow with:

```bash
bash scripts/run_weekly_codex_preflight.sh
```

Expected outputs:

- `Machine/Graph/graph.json`
- `Machine/Graph/GRAPH_REPORT.md`
- `Machine/Graph/retrieval-map.md`
- `Machine/Graph/codex-weekly-wiki.md`

These files are designed to help Codex retrieve vault context with fewer tokens.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
