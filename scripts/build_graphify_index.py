#!/usr/bin/env python3
"""
Build a lightweight graph index for this Obsidian vault.

The output is intentionally small and Codex-friendly:
- Machine/Graph/graph.json: structured nodes and edges
- Machine/Graph/GRAPH_REPORT.md: human-readable graph summary
- Machine/Graph/retrieval-map.md: first-stop retrieval guide for agents
- Machine/Graph/codex-weekly-wiki.md: weekly Codex feed in markdown wiki form

This is a local Graphify-compatible layer for automation. It does not require
external services or non-standard Python packages.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".obsidian/plugins",
    ".trash",
    "__pycache__",
    ".venv",
}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/-]+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
TASK_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)


@dataclass
class NoteNode:
    id: str
    path: str
    title: str
    type: str
    status: str
    tags: list[str]
    headings: list[str]
    open_tasks: int
    completed_tasks: int
    size_bytes: int
    modified_utc: str


@dataclass
class Edge:
    source: str
    target: str
    type: str
    label: str = ""


def should_skip(path: Path, root: Path, exclude_dirs: set[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(rel == item or rel.startswith(f"{item}/") for item in exclude_dirs)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    raw = text[4:end].splitlines()
    body = text[end + 5 :]
    data: dict[str, object] = {}
    current_key: str | None = None

    for line in raw:
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            value = str(line[4:]).strip().strip('"')
            existing = data.setdefault(current_key, [])
            if isinstance(existing, list):
                existing.append(value)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value == "":
                data[current_key] = []
            elif value.startswith("[") and value.endswith("]"):
                data[current_key] = [
                    item.strip().strip('"').strip("'")
                    for item in value[1:-1].split(",")
                    if item.strip()
                ]
            else:
                data[current_key] = value.strip('"')

    return data, body


def normalize_tag(tag: str) -> str:
    return tag.strip().lstrip("#")


def note_title(path: Path, frontmatter: dict[str, object], body: str) -> str:
    title = frontmatter.get("title")
    if isinstance(title, str) and title:
        return title

    match = HEADING_RE.search(body)
    if match:
        return match.group(2).strip()

    return path.stem


def find_markdown_files(root: Path, exclude_dirs: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if should_skip(path, root, exclude_dirs):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix().lower())


def build_alias_index(files: Iterable[Path], root: Path) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        aliases[rel] = rel
        aliases[rel.removesuffix(".md")] = rel
        aliases[path.stem] = rel
    return aliases


def resolve_wikilink(target: str, aliases: dict[str, str]) -> str:
    cleaned = target.strip()
    if cleaned in aliases:
        return aliases[cleaned]
    if f"{cleaned}.md" in aliases:
        return aliases[f"{cleaned}.md"]
    return cleaned


def collect_note(path: Path, root: Path) -> tuple[NoteNode, str, dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = parse_frontmatter(text)
    rel = path.relative_to(root).as_posix()

    fm_tags = frontmatter.get("tags", [])
    tags: set[str] = set()
    if isinstance(fm_tags, list):
        tags.update(normalize_tag(str(tag)) for tag in fm_tags if str(tag).strip())
    elif isinstance(fm_tags, str):
        tags.add(normalize_tag(fm_tags))
    tags.update(normalize_tag(tag) for tag in INLINE_TAG_RE.findall(body))

    tasks = TASK_RE.findall(body)
    headings = [match.group(2).strip() for match in HEADING_RE.finditer(body)]
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")

    node = NoteNode(
        id=rel,
        path=rel,
        title=note_title(path, frontmatter, body),
        type=str(frontmatter.get("type", "")),
        status=str(frontmatter.get("status", "")),
        tags=sorted(tags),
        headings=headings[:40],
        open_tasks=sum(1 for state, _ in tasks if state == " "),
        completed_tasks=sum(1 for state, _ in tasks if state.lower() == "x"),
        size_bytes=path.stat().st_size,
        modified_utc=modified,
    )
    return node, body, frontmatter


def build_graph(root: Path, out_dir: Path) -> dict[str, object]:
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if out_dir.is_relative_to(root):
        # Include reports in future runs only if they are useful; graph.json itself is skipped.
        exclude_dirs.add((out_dir / "graph.json").relative_to(root).as_posix())

    files = find_markdown_files(root, exclude_dirs)
    aliases = build_alias_index(files, root)
    nodes: list[NoteNode] = []
    edges: list[Edge] = []
    tag_counts: Counter[str] = Counter()
    folder_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    daily_notes: list[NoteNode] = []

    for path in files:
        node, body, _ = collect_note(path, root)
        nodes.append(node)

        folder = Path(node.path).parent.as_posix()
        folder_counts[folder if folder != "." else "/"] += 1
        if node.type:
            type_counts[node.type] += 1
        for tag in node.tags:
            tag_counts[tag] += 1
            edges.append(Edge(source=node.id, target=f"tag:{tag}", type="tag", label=tag))
        if node.path.startswith("daily_notes/"):
            daily_notes.append(node)

        for link in WIKILINK_RE.findall(body):
            target = resolve_wikilink(link, aliases)
            edges.append(Edge(source=node.id, target=target, type="wikilink"))

        for _, url in MARKDOWN_LINK_RE.findall(body):
            if url.startswith(("http://", "https://")):
                edges.append(Edge(source=node.id, target=url, type="external-link"))

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema": "obsidian-vault-graph-v1",
        "generated_at": generated_at,
        "root": root.name,
        "counts": {
            "notes": len(nodes),
            "edges": len(edges),
            "tags": len(tag_counts),
            "open_tasks": sum(node.open_tasks for node in nodes),
            "completed_tasks": sum(node.completed_tasks for node in nodes),
            "daily_notes": len(daily_notes),
        },
        "top_tags": tag_counts.most_common(20),
        "top_folders": folder_counts.most_common(20),
        "types": type_counts.most_common(20),
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
    }


def latest_by_prefix(nodes: list[dict[str, object]], prefix: str, limit: int = 5) -> list[dict[str, object]]:
    matching = [node for node in nodes if str(node["path"]).startswith(prefix)]
    return sorted(matching, key=lambda n: str(n["modified_utc"]), reverse=True)[:limit]


def write_report(graph: dict[str, object], out_dir: Path) -> None:
    counts = graph["counts"]
    nodes = graph["nodes"]
    assert isinstance(counts, dict)
    assert isinstance(nodes, list)

    lines: list[str] = [
        "---",
        "type: graph-report",
        "status: active",
        f"generated_at: {graph['generated_at']}",
        "tags:",
        "  - graph",
        "  - codex",
        "  - retrieval",
        "---",
        "",
        "# Graph Report",
        "",
        "## Summary",
        "",
        f"- Notes: {counts['notes']}",
        f"- Edges: {counts['edges']}",
        f"- Tags: {counts['tags']}",
        f"- Open tasks: {counts['open_tasks']}",
        f"- Completed tasks: {counts['completed_tasks']}",
        f"- Daily notes: {counts['daily_notes']}",
        "",
        "## Top Tags",
        "",
    ]

    top_tags = graph["top_tags"]
    assert isinstance(top_tags, list)
    if top_tags:
        for tag, count in top_tags[:15]:
            lines.append(f"- #{tag}: {count}")
    else:
        lines.append("- No tags found.")

    lines.extend(["", "## Top Folders", ""])
    top_folders = graph["top_folders"]
    assert isinstance(top_folders, list)
    for folder, count in top_folders[:15]:
        lines.append(f"- `{folder}`: {count}")

    lines.extend(["", "## Latest Daily Notes", ""])
    for node in latest_by_prefix(nodes, "daily_notes/", limit=7):
        lines.append(f"- [[{str(node['path']).removesuffix('.md')}|{node['title']}]]")

    lines.extend(["", "## Latest Trend Captures", ""])
    latest_trends = latest_by_prefix(nodes, "Inbox/GitHubTrending/", 3) + latest_by_prefix(nodes, "Inbox/HuggingFaceHub/", 3)
    if latest_trends:
        for node in latest_trends:
            lines.append(f"- [[{str(node['path']).removesuffix('.md')}|{node['title']}]]")
    else:
        lines.append("- No trend captures yet.")

    lines.append("")
    out_dir.joinpath("GRAPH_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def write_retrieval_map(graph: dict[str, object], out_dir: Path) -> None:
    nodes = graph["nodes"]
    assert isinstance(nodes, list)

    lines: list[str] = [
        "---",
        "type: retrieval-map",
        "status: active",
        f"generated_at: {graph['generated_at']}",
        "tags:",
        "  - codex",
        "  - retrieval",
        "  - graph",
        "---",
        "",
        "# Retrieval Map",
        "",
        "Use this map before opening raw notes.",
        "",
        "## Start Here",
        "",
        "- [[AGENTS]]",
        "- [[Machine/Context/Codex Retrieval Guide|Codex Retrieval Guide]]",
        "- [[Dashboard]]",
        "- [[Machine/Graph/GRAPH_REPORT|Graph Report]]",
        "- [[Machine/Graph/codex-weekly-wiki|Codex Weekly Wiki]]",
        "",
        "## Recent Daily Notes",
        "",
    ]

    for node in latest_by_prefix(nodes, "daily_notes/", limit=7):
        lines.append(f"- [[{str(node['path']).removesuffix('.md')}|{node['title']}]]")

    lines.extend(["", "## Raw Inputs", ""])
    for folder in [
        "Inbox/ChatGPT/",
        "Inbox/Codex/",
        "Inbox/Code/",
        "Inbox/GitHubTrending/",
        "Inbox/HuggingFaceHub/",
    ]:
        latest = latest_by_prefix(nodes, folder, limit=5)
        lines.append(f"### {folder}")
        if latest:
            for node in latest:
                lines.append(f"- [[{str(node['path']).removesuffix('.md')}|{node['title']}]]")
        else:
            lines.append("- No notes yet.")
        lines.append("")

    lines.extend(["## Research Outputs", ""])
    latest_research = latest_by_prefix(nodes, "Research/", limit=10)
    if latest_research:
        for node in latest_research:
            lines.append(f"- [[{str(node['path']).removesuffix('.md')}|{node['title']}]]")
    else:
        lines.append("- No research notes yet.")

    lines.append("")
    out_dir.joinpath("retrieval-map.md").write_text("\n".join(lines), encoding="utf-8")


def wiki_link(node: dict[str, object]) -> str:
    path = str(node["path"])
    title = str(node["title"])
    return f"- [[{path.removesuffix('.md')}|{title}]]"


def write_codex_weekly_wiki(graph: dict[str, object], out_dir: Path) -> None:
    counts = graph["counts"]
    nodes = graph["nodes"]
    assert isinstance(counts, dict)
    assert isinstance(nodes, list)

    lines: list[str] = [
        "---",
        "type: codex-weekly-feed",
        "status: active",
        f"generated_at: {graph['generated_at']}",
        "tags:",
        "  - codex",
        "  - weekly",
        "  - retrieval",
        "  - graph",
        "---",
        "",
        "# Codex Weekly Wiki",
        "",
        "Read this before running the Sunday A2A Trend Council. It is regenerated by `scripts/update_graphify_index.sh` after Graphify runs with `--wiki`.",
        "",
        "## Required First Reads",
        "",
        "- [[Machine/Context/Codex Retrieval Guide|Codex Retrieval Guide]]",
        "- [[Machine/Automation/Prompts/Cloud Automation Prompts|Cloud Automation Prompts]]",
        "- [[Machine/Graph/retrieval-map|Retrieval Map]]",
        "- [[Machine/Graph/GRAPH_REPORT|Graph Report]]",
        "- [[Dashboard]]",
        "- [[Machine/Automation/Runbooks/Ubuntu VPS Cron Setup|Ubuntu VPS Cron Setup]]",
        "- `graphify-out/GRAPH_REPORT.md` when present",
        "",
        "## Graph Snapshot",
        "",
        f"- Generated: `{graph['generated_at']}`",
        f"- Notes: {counts['notes']}",
        f"- Edges: {counts['edges']}",
        f"- Tags: {counts['tags']}",
        f"- Open tasks: {counts['open_tasks']}",
        f"- Completed tasks: {counts['completed_tasks']}",
        "",
        "## Recent Daily Notes",
        "",
    ]

    recent_daily = latest_by_prefix(nodes, "daily_notes/", limit=7)
    if recent_daily:
        lines.extend(wiki_link(node) for node in recent_daily)
    else:
        lines.append("- No daily notes found.")

    sections = [
        ("Recent GitHub Trend Captures", "Inbox/GitHubTrending/", 4),
        ("Recent Hugging Face Trend Captures", "Inbox/HuggingFaceHub/", 4),
        ("Recent Codex Captures", "Inbox/Codex/", 4),
        ("Recent ChatGPT Captures", "Inbox/ChatGPT/", 4),
        ("Recent Code Captures", "Inbox/Code/", 4),
        ("Recent Daily Agent Outputs", "Research/daily-agent/", 5),
        ("Recent Weekend Agent Outputs", "Research/weekend-agent/", 5),
        ("Source Targets", "Sources/", 10),
    ]

    for title, prefix, limit in sections:
        lines.extend(["", f"## {title}", ""])
        latest = latest_by_prefix(nodes, prefix, limit=limit)
        if latest:
            lines.extend(wiki_link(node) for node in latest)
        else:
            lines.append("- No notes found.")

    lines.extend(
        [
            "",
            "## Weekly Council Routing",
            "",
            "- Use graph/retrieval outputs to choose raw files; do not read every raw trend capture by default.",
            "- Compare trend candidates against recent daily notes, blockers, TODOs, and source targets.",
            "- Separate recommendations into try now, watch later, and ignore.",
            "- Preserve raw notes and handwritten notes.",
            "",
            "## VPS Cron Command",
            "",
            "```bash",
            "cd /path/to/ObsidianVaultV1",
            "bash scripts/run_weekly_codex_preflight.sh",
            "```",
            "",
            "## Reference Intake",
            "",
            "- Do not use X/Twitter as a live source for trend research.",
            "- If the user pastes content from X/Twitter, treat it as unverified inspiration and verify the underlying claims through primary or non-X sources.",
            "",
        ]
    )

    out_dir.joinpath("codex-weekly-wiki.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-dir", default="Machine/Graph")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    graph = build_graph(root, out_dir)
    out_dir.joinpath("graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(graph, out_dir)
    write_retrieval_map(graph, out_dir)
    write_codex_weekly_wiki(graph, out_dir)

    counts = graph["counts"]
    print(
        "Built graph index: "
        f"{counts['notes']} notes, {counts['edges']} edges, {counts['open_tasks']} open tasks"
    )


if __name__ == "__main__":
    main()
