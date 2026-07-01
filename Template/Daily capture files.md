# Definition in template:
Focus = what matters
Goals = what should be true by tonight
Tasks = general checklist
Coding tasks = dev checklist
Calendar / hard stops = time boundaries
# Daily Raw Capture Files

Every day, create files like:

```text
Inbox/ChatGPT/2026/06/24.md
Inbox/Codex/2026/06/24.md
Inbox/Code/2026/06/24.md
Inbox/GitHubTrending/2026/06/24.md
Inbox/HuggingFaceHub/2026/06/24.md
daily_notes/2026/06/24.md
```

In `Inbox/ChatGPT/YYYY/MM/DD.md`, paste useful ChatGPT conversations/searches.

In `Inbox/Codex/YYYY/MM/DD.md`, paste useful Codex prompts, code changes, errors, and solutions.

In `Inbox/Code/YYYY/MM/DD.md`, paste output like:

```bash
git log --since="today" --stat
git diff --name-only
git diff --stat
```

# Evening Update Prompt

Read these notes:

- `AGENTS.md`
- `Machine/Context/Codex Retrieval Guide.md`
- `Machine/Graph/retrieval-map.md` if it exists
- `daily_notes/2026/06/24.md`
- `Inbox/ChatGPT/2026/06/24.md` if it exists
- `Inbox/Codex/2026/06/24.md` if it exists
- `Inbox/Code/2026/06/24.md` if it exists
- `Inbox/GitHubTrending/2026/06/24.md` if it exists
- `Inbox/HuggingFaceHub/2026/06/24.md` if it exists

Task:

Update only the `## End of day` section in `daily_notes/2026/06/24.md`.

Rules:

- Preserve `## Start of day` exactly.
- Do not overwrite handwritten notes.
- Do not include raw conversation logs.
- Summarize high-signal learning only.
- Focus on what I learned, coded, debugged, and should continue tomorrow.
- Prioritize AI, NLP, LLM, agents, software engineering, and coding lessons.

Output structure:

```text
### What I searched today
### What I learned
### What I coded
### New methods / tools / concepts
### Bugs / blockers
### Reusable snippets
### Tomorrow follow-up
### Human reflection
```
