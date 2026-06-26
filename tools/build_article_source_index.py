#!/usr/bin/env python3
"""Create an article-to-source index from a meeting manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_PATTERN = re.compile(r"\barticles?\s+([0-9]+[a-z]?)\b", re.IGNORECASE)
ARTICLE_RANGE_PATTERN = re.compile(
    r"\barticles?\s+([0-9]+[a-z]?)\s+(?:through|to|-)\s+([0-9]+[a-z]?)\b",
    re.IGNORECASE,
)


INDEXED_CATEGORIES = {
    "finance_committee",
    "minutes_or_actions",
    "motion_or_amendment",
    "presentation",
    "related_document",
    "warrant",
}


def article_sort_key(article_id: str) -> tuple[int, str]:
    match = re.fullmatch(r"([0-9]+)([a-z]?)", article_id.casefold())
    if not match:
        return (9999, article_id)
    return (int(match.group(1)), match.group(2))


def expand_range(start: str, end: str) -> list[str]:
    start_match = re.fullmatch(r"([0-9]+)([a-z]?)", start.casefold())
    end_match = re.fullmatch(r"([0-9]+)([a-z]?)", end.casefold())
    if not start_match or not end_match or start_match.group(2) or end_match.group(2):
        return [start.upper(), end.upper()]
    start_num = int(start_match.group(1))
    end_num = int(end_match.group(1))
    if end_num < start_num or end_num - start_num > 100:
        return [start.upper(), end.upper()]
    return [str(value) for value in range(start_num, end_num + 1)]


def article_ids_from_title(title: str) -> list[str]:
    found: set[str] = set()
    for match in ARTICLE_RANGE_PATTERN.finditer(title):
        found.update(expand_range(match.group(1), match.group(2)))
    for match in ARTICLE_PATTERN.finditer(title):
        found.add(match.group(1).upper())
    return sorted(found, key=article_sort_key)


def source_summary(source: dict[str, object]) -> dict[str, object]:
    return {
        "id": source["id"],
        "title": source["title"],
        "category": source["category"],
        "url": source["url"],
        "official": source["official"],
        "status": source["status"],
        "local_path": source.get("local_path", ""),
    }


def build_index(manifest: dict[str, object]) -> dict[str, object]:
    articles: dict[str, dict[str, object]] = {}
    meeting_level_sources: list[dict[str, object]] = []
    uncategorized_article_sources: list[dict[str, object]] = []

    for source in manifest["sources"]:
        category = str(source["category"])
        if category not in INDEXED_CATEGORIES:
            continue
        if category in {"warrant", "finance_committee", "minutes_or_actions"}:
            meeting_level_sources.append(source_summary(source))
        article_ids = article_ids_from_title(str(source["title"]))
        if not article_ids:
            if category in {"motion_or_amendment", "presentation", "related_document"}:
                uncategorized_article_sources.append(source_summary(source))
            continue
        for article_id in article_ids:
            article = articles.setdefault(
                article_id,
                {
                    "article": article_id,
                    "sources": [],
                    "open_items": [],
                },
            )
            article["sources"].append(source_summary(source))

    for article in articles.values():
        article["sources"].sort(key=lambda item: (item["category"], item["title"]))
        if not any(item["category"] == "motion_or_amendment" for item in article["sources"]):
            article["open_items"].append("No article-specific motion or amendment source identified by title.")
        if not any(item["category"] == "presentation" for item in article["sources"]):
            article["open_items"].append("No article-specific sponsor presentation source identified by title.")

    return {
        "meeting_id": manifest["meeting_id"],
        "generated_from": "manifest.json",
        "article_count_from_source_titles": len(articles),
        "articles": [articles[key] for key in sorted(articles, key=article_sort_key)],
        "meeting_level_sources": meeting_level_sources,
        "uncategorized_article_sources": uncategorized_article_sources,
        "open_items": [
            "This index uses article numbers found in source titles only.",
            "Parse the official warrant and motion documents to confirm article titles and complete article coverage.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    index = build_index(manifest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Articles indexed: {index['article_count_from_source_titles']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
