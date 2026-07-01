#!/usr/bin/env python3
"""
Collect Python GitHub Trending repositories by crawling the public GitHub Trending page.

Pages collected:
- https://github.com/trending/python?since=weekly
- https://github.com/trending/python?since=monthly

This script only captures raw trend data.
Codex will analyze the Markdown later.
"""

from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


GITHUB_BASE = "https://github.com"
LANGUAGE = "python"
DEFAULT_WINDOWS = ["weekly", "monthly"]


@dataclass(frozen=True)
class TrendingRepo:
    window: str
    rank: int
    full_name: str
    url: str
    description: str
    primary_language: str
    stars: str
    forks: str
    stars_this_period: str
    built_by: list[str]


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_repo_article(article, *, window: str, rank: int) -> TrendingRepo | None:
    title_link = article.select_one("h2 a")
    if not title_link:
        return None

    href = title_link.get("href", "")
    full_name = clean_text(title_link.get_text()).replace(" / ", "/")
    url = urljoin(GITHUB_BASE, href)

    desc_el = article.select_one("p")
    description = clean_text(desc_el.get_text()) if desc_el else ""

    language_el = article.select_one("[itemprop='programmingLanguage']")
    primary_language = clean_text(language_el.get_text()) if language_el else ""

    footer_links = article.select("a.Link--muted")
    stars = clean_text(footer_links[0].get_text()) if len(footer_links) > 0 else ""
    forks = clean_text(footer_links[1].get_text()) if len(footer_links) > 1 else ""

    period_el = article.select_one("span.d-inline-block.float-sm-right")
    stars_this_period = clean_text(period_el.get_text()) if period_el else ""

    built_by: list[str] = []
    for avatar in article.select("img.avatar"):
        alt = avatar.get("alt", "")
        if alt.startswith("@"):
            built_by.append(alt)

    return TrendingRepo(
        window=window,
        rank=rank,
        full_name=full_name,
        url=url,
        description=description,
        primary_language=primary_language,
        stars=stars,
        forks=forks,
        stars_this_period=stars_this_period,
        built_by=built_by,
    )


def fetch_trending(window: str, *, sleep_seconds: float = 2.0) -> list[TrendingRepo]:
    url = f"{GITHUB_BASE}/trending/{LANGUAGE}?since={window}"

    headers = {
        "User-Agent": "ObsidianVaultV1-GitHubTrendingCollector/1.0",
        "Accept": "text/html,application/xhtml+xml",
    }

    print(f"Fetching {url}")

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    # Be gentle.
    time.sleep(sleep_seconds)

    soup = BeautifulSoup(response.text, "html.parser")

    repos: list[TrendingRepo] = []

    for idx, article in enumerate(soup.select("article.Box-row"), start=1):
        repo = parse_repo_article(article, window=window, rank=idx)
        if repo:
            repos.append(repo)

    return repos


def format_markdown(repos: Iterable[TrendingRepo], *, generated_at: str) -> str:
    repos = list(repos)

    lines: list[str] = []
    lines.append("---")
    lines.append("type: github-trending-python-raw")
    lines.append(f"generated_at: {generated_at}")
    lines.append("source: github-trending-html")
    lines.append("language: python")
    lines.append("tags:")
    lines.append("  - github-trending")
    lines.append("  - python")
    lines.append("  - ai-trends")
    lines.append("  - ai-engineering")
    lines.append("---")
    lines.append("")
    lines.append(f"# GitHub Trending Python Raw - {generated_at[:10]}")
    lines.append("")
    lines.append("> Raw GitHub Trending capture from the public Python trending page.")
    lines.append("> Codex should analyze this later and extract useful AI/LLM/NLP/agent trends.")
    lines.append("")

    grouped: dict[str, list[TrendingRepo]] = {}
    for repo in repos:
        grouped.setdefault(repo.window, []).append(repo)

    for window in DEFAULT_WINDOWS:
        group = grouped.get(window, [])
        lines.append(f"## {window.title()} Python Trending")
        lines.append("")

        if not group:
            lines.append("> No repositories collected.")
            lines.append("")
            continue

        for repo in group:
            lines.append(f"### {repo.rank}. [{repo.full_name}]({repo.url})")
            lines.append("")
            if repo.description:
                lines.append(f"- Description: {repo.description}")
            if repo.primary_language:
                lines.append(f"- Language: {repo.primary_language}")
            if repo.stars:
                lines.append(f"- Stars: {repo.stars}")
            if repo.forks:
                lines.append(f"- Forks: {repo.forks}")
            if repo.stars_this_period:
                lines.append(f"- Stars this period: {repo.stars_this_period}")
            if repo.built_by:
                lines.append(f"- Built by: {', '.join(repo.built_by[:10])}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="Inbox/GitHubTrending")
    parser.add_argument("--date", help="Output date in YYYY-MM-DD format. Defaults to the current local date.")
    parser.add_argument("--sleep-seconds", type=float, default=2.0)
    parser.add_argument("--windows", nargs="*", default=DEFAULT_WINDOWS)
    args = parser.parse_args()

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    generated_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.fromisoformat(generated_at)

    all_repos: list[TrendingRepo] = []

    for window in args.windows:
        try:
            all_repos.extend(fetch_trending(window, sleep_seconds=args.sleep_seconds))
        except Exception as exc:
            print(f"WARNING: failed to fetch GitHub Trending window={window}: {exc}")

    out_dir = Path(args.out_dir) / generated_date.strftime("%Y/%m")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{generated_date:%d}.md"
    out_path.write_text(format_markdown(all_repos, generated_at=generated_at), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Collected {len(all_repos)} repository entries")


if __name__ == "__main__":
    main()
