#!/usr/bin/env python3
"""
Collect Hugging Face Hub trend signals and write them into an Obsidian Markdown note.

Sources:
- Trending models
- Trending datasets
- Trending Spaces
- Trending daily papers
- Topic-based model searches sorted by trend score

This script does not use an LLM.
Codex analyzes the raw note later.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from huggingface_hub import HfApi


HF_BASE = "https://huggingface.co"

TOPIC_QUERIES = [
    "llm",
    "agent",
    "rag",
    "embedding",
    "reranker",
    "nlp",
    "text-generation",
    "speech",
    "asr",
    "tts",
    "ocr",
    "document parsing",
    "vision language",
    "multimodal",
    "evaluation",
    "benchmark",
    "fine-tuning",
    "quantization",
]


@dataclass(frozen=True)
class HubItem:
    section: str
    rank: int
    item_type: str
    repo_id: str
    url: str
    likes: str
    downloads: str
    trending_score: str
    last_modified: str
    tags: list[str]


def get_attr(obj: Any, *names: str, default: Any = "") -> Any:
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return default


def format_dt(value: Any) -> str:
    if not value:
        return ""
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def safe_int_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def model_to_item(model: Any, *, section: str, rank: int) -> HubItem:
    repo_id = get_attr(model, "id", "modelId", default="")
    tags = get_attr(model, "tags", default=[]) or []

    return HubItem(
        section=section,
        rank=rank,
        item_type="model",
        repo_id=repo_id,
        url=f"{HF_BASE}/{repo_id}" if repo_id else "",
        likes=safe_int_str(get_attr(model, "likes", default="")),
        downloads=safe_int_str(get_attr(model, "downloads", default="")),
        trending_score=safe_int_str(get_attr(model, "trending_score", "trendingScore", default="")),
        last_modified=format_dt(get_attr(model, "last_modified", "lastModified", default="")),
        tags=list(tags)[:20],
    )


def dataset_to_item(dataset: Any, *, section: str, rank: int) -> HubItem:
    repo_id = get_attr(dataset, "id", default="")
    tags = get_attr(dataset, "tags", default=[]) or []

    return HubItem(
        section=section,
        rank=rank,
        item_type="dataset",
        repo_id=repo_id,
        url=f"{HF_BASE}/datasets/{repo_id}" if repo_id else "",
        likes=safe_int_str(get_attr(dataset, "likes", default="")),
        downloads=safe_int_str(get_attr(dataset, "downloads", default="")),
        trending_score=safe_int_str(get_attr(dataset, "trending_score", "trendingScore", default="")),
        last_modified=format_dt(get_attr(dataset, "last_modified", "lastModified", default="")),
        tags=list(tags)[:20],
    )


def space_to_item(space: Any, *, section: str, rank: int) -> HubItem:
    repo_id = get_attr(space, "id", default="")
    tags = get_attr(space, "tags", default=[]) or []

    return HubItem(
        section=section,
        rank=rank,
        item_type="space",
        repo_id=repo_id,
        url=f"{HF_BASE}/spaces/{repo_id}" if repo_id else "",
        likes=safe_int_str(get_attr(space, "likes", default="")),
        downloads="",
        trending_score=safe_int_str(get_attr(space, "trending_score", "trendingScore", default="")),
        last_modified=format_dt(get_attr(space, "last_modified", "lastModified", default="")),
        tags=list(tags)[:20],
    )


def fetch_models(api: HfApi, *, limit: int) -> list[HubItem]:
    models = list(
        api.list_models(
            sort="trending_score",
            limit=limit,
            expand=["downloads", "likes", "tags", "lastModified", "trendingScore", "pipeline_tag"],
            token=os.getenv("HF_TOKEN") or False,
        )
    )

    return [model_to_item(model, section="Trending Models", rank=i) for i, model in enumerate(models, start=1)]


def fetch_topic_models(api: HfApi, *, limit_per_topic: int) -> list[HubItem]:
    items: list[HubItem] = []

    for topic in TOPIC_QUERIES:
        try:
            models = list(
                api.list_models(
                    search=topic,
                    sort="trending_score",
                    limit=limit_per_topic,
                    expand=["downloads", "likes", "tags", "lastModified", "trendingScore", "pipeline_tag"],
                    token=os.getenv("HF_TOKEN") or False,
                )
            )
        except Exception as exc:
            print(f"WARNING: failed topic model search {topic}: {exc}")
            continue

        for i, model in enumerate(models, start=1):
            items.append(model_to_item(model, section=f"Topic Models - {topic}", rank=i))

    return items


def fetch_datasets(api: HfApi, *, limit: int) -> list[HubItem]:
    datasets = list(
        api.list_datasets(
            sort="trending_score",
            limit=limit,
            expand=["downloads", "likes", "tags", "lastModified", "trendingScore"],
            token=os.getenv("HF_TOKEN") or False,
        )
    )

    return [dataset_to_item(dataset, section="Trending Datasets", rank=i) for i, dataset in enumerate(datasets, start=1)]


def fetch_spaces(api: HfApi, *, limit: int) -> list[HubItem]:
    spaces = list(
        api.list_spaces(
            sort="trending_score",
            limit=limit,
            expand=["likes", "tags", "lastModified", "trendingScore", "sdk"],
            token=os.getenv("HF_TOKEN") or False,
        )
    )

    return [space_to_item(space, section="Trending Spaces", rank=i) for i, space in enumerate(spaces, start=1)]


def format_papers(api: HfApi, *, limit: int) -> list[str]:
    lines: list[str] = []
    lines.append("## Trending Daily Papers")
    lines.append("")

    try:
        papers = list(
            api.list_daily_papers(
                sort="trending",
                limit=limit,
                token=os.getenv("HF_TOKEN") or False,
            )
        )
    except Exception as exc:
        lines.append(f"> Failed to fetch daily papers: {exc}")
        lines.append("")
        return lines

    for i, paper in enumerate(papers, start=1):
        paper_id = get_attr(paper, "id", "paper_id", default="")
        title = get_attr(paper, "title", default=paper_id)
        summary = get_attr(paper, "summary", default="")
        published_at = format_dt(get_attr(paper, "published_at", "publishedAt", default=""))
        url = f"{HF_BASE}/papers/{paper_id}" if paper_id else ""

        lines.append(f"### {i}. [{title}]({url})")
        lines.append("")
        if paper_id:
            lines.append(f"- Paper ID: {paper_id}")
        if published_at:
            lines.append(f"- Published: {published_at}")
        if summary:
            lines.append(f"- Summary: {summary[:600].strip()}")
        lines.append("")

    return lines


def format_items(items: Iterable[HubItem]) -> list[str]:
    items = list(items)
    lines: list[str] = []

    grouped: dict[str, list[HubItem]] = {}
    for item in items:
        grouped.setdefault(item.section, []).append(item)

    for section, group in grouped.items():
        lines.append(f"## {section}")
        lines.append("")

        for item in group:
            title = item.repo_id or "unknown"
            lines.append(f"### {item.rank}. [{title}]({item.url})")
            lines.append("")
            lines.append(f"- Type: {item.item_type}")
            if item.likes:
                lines.append(f"- Likes: {item.likes}")
            if item.downloads:
                lines.append(f"- Downloads: {item.downloads}")
            if item.trending_score:
                lines.append(f"- Trending score: {item.trending_score}")
            if item.last_modified:
                lines.append(f"- Last modified: {item.last_modified}")
            if item.tags:
                lines.append(f"- Tags: {', '.join(item.tags[:12])}")
            lines.append("")

    return lines


def build_markdown(api: HfApi, *, generated_at: str, limit: int, topic_limit: int) -> str:
    items: list[HubItem] = []

    for fetcher in [
        lambda: fetch_models(api, limit=limit),
        lambda: fetch_datasets(api, limit=limit),
        lambda: fetch_spaces(api, limit=limit),
        lambda: fetch_topic_models(api, limit_per_topic=topic_limit),
    ]:
        try:
            items.extend(fetcher())
        except Exception as exc:
            print(f"WARNING: fetcher failed: {exc}")

    lines: list[str] = []
    lines.append("---")
    lines.append("type: hf-hub-trends-raw")
    lines.append(f"generated_at: {generated_at}")
    lines.append("tags:")
    lines.append("  - huggingface")
    lines.append("  - ai-trends")
    lines.append("  - ai-engineering")
    lines.append("---")
    lines.append("")
    lines.append(f"# Hugging Face Hub Trends Raw - {generated_at[:10]}")
    lines.append("")
    lines.append("> Raw Hugging Face Hub trend capture. Codex should analyze this later for useful AI/LLM/NLP/agent learning signals.")
    lines.append("")

    lines.extend(format_items(items))
    lines.extend(format_papers(api, limit=limit))

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="Inbox/HuggingFaceHub")
    parser.add_argument("--date", help="Output date in YYYY-MM-DD format. Defaults to the current local date.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--topic-limit", type=int, default=8)
    args = parser.parse_args()

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    generated_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.fromisoformat(generated_at)

    api = HfApi(token=os.getenv("HF_TOKEN") or False)

    out_dir = Path(args.out_dir) / generated_date.strftime("%Y/%m")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{generated_date:%d}.md"
    out_path.write_text(
        build_markdown(
            api,
            generated_at=generated_at,
            limit=args.limit,
            topic_limit=args.topic_limit,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
