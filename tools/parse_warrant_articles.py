#!/usr/bin/env python3
"""Parse article records from extracted warrant text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_HEADING = re.compile(
    r"^A?\s*rtic\s*le\s+([0-9](?:\s*[0-9]){0,2}[A-Z]?)\s*$",
    re.IGNORECASE,
)
PAGE_MARKER = re.compile(r"^--- Page [0-9]+ ---$")
SPONSOR_LINE = re.compile(r"^\(([^()]*)\)$")


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def normalize_text(text: str) -> str:
    text = text.replace("\ufb01", "fi").replace("\ufb00", "ff")
    text = re.sub(r"Fiscal Y ear", "Fiscal Year", text)
    return text


def body_start_index(lines: list[str]) -> int:
    matches = [index for index, line in enumerate(lines) if ARTICLE_HEADING.match(line)]
    for index in range(1, len(matches)):
        previous = ARTICLE_HEADING.match(lines[matches[index - 1]])
        current = ARTICLE_HEADING.match(lines[matches[index]])
        if previous and current and article_id(previous) == article_id(current):
            return matches[index]
    return matches[0] if matches else 0


def heading_indices(lines: list[str], start: int) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for index in range(start, len(lines)):
        match = ARTICLE_HEADING.match(lines[index])
        if match:
            result.append((index, article_id(match)))
    return result


def article_id(match: re.Match[str]) -> str:
    return re.sub(r"\s+", "", match.group(1)).upper()


def parse_article(article_id: str, raw_lines: list[str]) -> dict[str, object]:
    lines = [
        normalize_line(line)
        for line in raw_lines
        if normalize_line(line) and not PAGE_MARKER.match(normalize_line(line))
    ]
    title_lines: list[str] = []
    sponsor = ""
    body_start = 0

    for index, line in enumerate(lines):
        sponsor_match = SPONSOR_LINE.match(line)
        if sponsor_match:
            sponsor = sponsor_match.group(1)
            body_start = index + 1
            break
        title_lines.append(line)
    else:
        body_start = len(title_lines)

    title = normalize_line(" ".join(title_lines))
    warrant_text = normalize_line(" ".join(lines[body_start:]))
    return {
        "article": article_id,
        "title": title,
        "sponsor": sponsor,
        "warrant_text": warrant_text,
        "status": "parsed_from_warrant",
        "open_items": [
            "Confirm article title, sponsor, and text against the official warrant PDF.",
            "Attach article-specific motions, amendments, recommendations, and final action sources.",
        ],
    }


def parse_warrant(text: str) -> list[dict[str, object]]:
    lines = [normalize_line(line) for line in normalize_text(text).splitlines()]
    start = body_start_index(lines)
    headings = heading_indices(lines, start)
    articles: list[dict[str, object]] = []

    for position, (line_index, article_id) in enumerate(headings):
        next_index = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        raw_article_lines = lines[line_index + 1 : next_index]
        article = parse_article(article_id, raw_article_lines)
        if article["title"] or article["warrant_text"]:
            articles.append(article)
    return articles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--meeting-id", required=True)
    args = parser.parse_args()

    source_text = Path(args.input).read_text(encoding="utf-8")
    articles = parse_warrant(source_text)
    output = {
        "meeting_id": args.meeting_id,
        "source_text_path": args.input,
        "article_count": len(articles),
        "articles": articles,
        "open_items": [
            "This parser uses extracted PDF text and should be reviewer-checked.",
            "The next feature should merge these article records with the manifest article-source index.",
        ],
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Articles parsed: {len(articles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
