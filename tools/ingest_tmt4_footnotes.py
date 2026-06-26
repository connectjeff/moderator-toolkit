#!/usr/bin/env python3
"""Ingest the official TMT4 footnote resource table."""

from __future__ import annotations

import argparse
import datetime as dt
import html.parser
import json
import re
import sys
import urllib.request
from pathlib import Path


class FootnoteTableParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_tr = False
        self.in_td = False
        self.in_th = False
        self.current_cell = ""
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif self.in_tr and tag in {"td", "th"}:
            self.in_td = tag == "td"
            self.in_th = tag == "th"
            self.current_cell = ""
        elif self.in_tr and tag == "a":
            attrs_dict = {name: value or "" for name, value in attrs}
            href = attrs_dict.get("href")
            if href:
                self.current_cell += f" {href} "

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and (self.in_td or self.in_th):
            self.current_row.append(normalize_space(self.current_cell))
            self.current_cell = ""
            self.in_td = False
            self.in_th = False
        elif tag == "tr" and self.in_tr:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_tr = False

    def handle_data(self, data: str) -> None:
        if self.in_td or self.in_th:
            self.current_cell += data


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fetch_html(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TownModeratorToolkit/0.1 (+official-tmt4-footnotes)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_rows(html: str) -> list[dict[str, str]]:
    parser = FootnoteTableParser()
    parser.feed(html)
    entries: list[dict[str, str]] = []
    for row in parser.rows:
        if len(row) < 3:
            continue
        if row[0].casefold() in {"section", "§"}:
            continue
        url = clean_url_cell(row[2])
        if not url.startswith("http"):
            continue
        entries.append(
            {
                "section": row[0],
                "footnote": row[1],
                "url": url,
            }
        )
    return entries


def clean_url_cell(value: str) -> str:
    urls = re.findall(r"https?://\S+", value)
    if not urls:
        return value.strip()
    unique_urls: list[str] = []
    for url in urls:
        if url not in unique_urls:
            unique_urls.append(url)
    return " ".join(unique_urls)


def write_markdown(entries: list[dict[str, str]], output: Path, source_url: str, retrieved_at: str) -> None:
    lines = [
        "# TMT4 Footnote Sources",
        "",
        "Official source: https://massmoderators.org/tmt4-footnote/",
        f"Retrieved: {retrieved_at}",
        "",
        "These are web resources footnoted in Town Meeting Time, 4th edition, as published by the Massachusetts Moderators Association.",
        "",
        "| Section | Footnote | URL |",
        "| --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(f"| {entry['section']} | {entry['footnote']} | {entry['url']} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://massmoderators.org/tmt4-footnote/")
    parser.add_argument("--json-output", default="data/sources/tmt4-footnotes.json")
    parser.add_argument("--markdown-output", default="data/sources/tmt4-footnotes.md")
    args = parser.parse_args()

    try:
        html = fetch_html(args.url)
        entries = parse_rows(html)
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        payload = {
            "source_title": "Town Meeting Time Footnotes",
            "source_url": args.url,
            "retrieved_at": now,
            "official": True,
            "publisher": "Massachusetts Moderators Association",
            "entry_count": len(entries),
            "entries": entries,
        }
        json_output = Path(args.json_output)
        markdown_output = Path(args.markdown_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_markdown(entries, markdown_output, args.url, now)
    except Exception as exc:  # noqa: BLE001 - command-line tool should report all failures.
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.markdown_output}")
    print(f"Entries: {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
