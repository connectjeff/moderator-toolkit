#!/usr/bin/env python3
"""Build a source manifest from an official Natick Town Meeting page."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html.parser
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


SECTION_ALIASES = {
    "related documents": "related_document",
    "motions & amendments": "motion_or_amendment",
    "motions and amendments": "motion_or_amendment",
    "sponsor presentations": "presentation",
    "minutes & actions": "minutes_or_actions",
    "minutes and actions": "minutes_or_actions",
    "resource materials": "resource",
}


RELEVANT_PAGE_LINK_PATTERNS = (
    "vote",
    "voting result",
    "town meeting",
)


IGNORED_EXACT_TITLES = {
    "alert:",
    "alerts",
    "alerts & notifications",
    "bids / rfps",
    "calendar",
    "civicplus®",
    "community",
    "contact us",
    "create a website account",
    "departments",
    "employment",
    "faqs",
    "government",
    "home",
    "i want to...",
    "jobs / employment",
    "moderator",
    "news",
    "notify me®",
    "online payments",
    "permits & licenses",
    "property values",
    "quick links",
    "report a concern",
    "skip to main content",
    "town meeting information",
    "trash & recycling",
    "volunteer",
    "website sign in",
}


IGNORED_TITLE_PATTERNS = (
    "mandatory ban on",
    "water use restrictions",
)


DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
}


class NatickMeetingPageParser(html.parser.HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.current_heading: str | None = None
        self._heading_candidate: str | None = None
        self._active_link: dict[str, str] | None = None
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if re.fullmatch(r"h[1-6]", tag):
            self._heading_candidate = ""
        if tag == "a" and attrs_dict.get("href"):
            self._active_link = {
                "href": urllib.parse.urljoin(self.base_url, attrs_dict["href"]),
                "text": "",
                "section": self.current_heading or "page",
            }

    def handle_endtag(self, tag: str) -> None:
        if re.fullmatch(r"h[1-6]", tag) and self._heading_candidate is not None:
            heading = normalize_space(self._heading_candidate)
            if heading:
                self.current_heading = heading
            self._heading_candidate = None
        if tag == "a" and self._active_link is not None:
            text = normalize_space(self._active_link["text"])
            href = self._active_link["href"]
            if text and not is_navigation_link(text, href):
                self.links.append(
                    {
                        "title": text,
                        "url": href,
                        "section": self._active_link["section"],
                    }
                )
            self._active_link = None

    def handle_data(self, data: str) -> None:
        if self._heading_candidate is not None:
            self._heading_candidate += data
        if self._active_link is not None:
            self._active_link["text"] += data


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def is_navigation_link(text: str, href: str) -> bool:
    lowered = text.casefold()
    if lowered in IGNORED_EXACT_TITLES:
        return True
    if any(pattern in lowered for pattern in IGNORED_TITLE_PATTERNS):
        return True
    parsed = urllib.parse.urlparse(href)
    if parsed.scheme in {"mailto", "tel", "javascript"}:
        return True
    if "connect.civicplus.com" in parsed.netloc:
        return True
    return False


def is_relevant_link(title: str, section: str, url: str) -> bool:
    section_category = section_category_for_heading(section)
    if section_category:
        return True
    lowered = title.casefold()
    if any(pattern in lowered for pattern in RELEVANT_PAGE_LINK_PATTERNS):
        return True
    return "/DocumentCenter/View/" in urllib.parse.urlparse(url).path


def source_type_for_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    suffix = Path(path).suffix.casefold()
    if "/DocumentCenter/View/" in path:
        return "document"
    if suffix in {".xls", ".xlsx"}:
        return "spreadsheet"
    if suffix in {".ppt", ".pptx"}:
        return "presentation"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    if "youtube.com" in url or "youtu.be" in url or "peg.tv" in url or "telvue.com" in url:
        return "video"
    if urllib.parse.urlparse(url).scheme in {"http", "https"}:
        return "web_page"
    return "unknown"


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or fallback


def section_category_for_heading(section: str) -> str | None:
    normalized_section = section.casefold()
    for heading, category in SECTION_ALIASES.items():
        if heading in normalized_section:
            return category
    return None


def category_for_link(title: str, section: str, url: str) -> str:
    normalized_title = title.casefold()
    section_category = section_category_for_heading(section)
    if normalized_title == "town meeting motion form":
        return section_category or "resource"
    if "warrant" in normalized_title:
        return "warrant"
    if "fincom" in normalized_title or "finance committee" in normalized_title:
        return "finance_committee"
    if "motion" in normalized_title or "amendment" in normalized_title:
        return "motion_or_amendment"
    if "presentation" in normalized_title:
        return "presentation"
    if "minutes" in normalized_title or "report" in normalized_title or "vote" in normalized_title:
        return "minutes_or_actions"
    if section_category:
        return section_category
    return "resource"


def is_official_natick_source(url: str, official_page_url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    official_page = urllib.parse.urlparse(official_page_url)
    if parsed.netloc == "sites.google.com" and parsed.path.startswith("/natickma.org/"):
        return True
    if parsed.netloc == official_page.netloc:
        return True
    if parsed.netloc.endswith("natickma.gov"):
        return True
    if parsed.netloc.endswith("massmoderators.org"):
        return True
    if parsed.netloc.endswith("natickma.org"):
        return True
    if parsed.netloc.endswith("archives.gov"):
        return True
    if parsed.netloc.endswith("malegislature.gov"):
        return True
    return False


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TownModeratorToolkit/0.1 (+official-source-manifest)",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def build_manifest(args: argparse.Namespace, html: str) -> dict[str, object]:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    parser = NatickMeetingPageParser(args.url)
    parser.feed(html)

    seen: set[str] = set()
    sources: list[dict[str, object]] = [
        {
            "id": "official-meeting-page",
            "title": args.title,
            "url": args.url,
            "category": "meeting_page",
            "source_type": "web_page",
            "official": True,
            "listed_on_official_page": True,
            "retrieved_at": now.isoformat(),
            "local_path": "sources/official-meeting-page.html",
            "status": "archived",
            "notes": "Official Natick Town Meeting page used as source manifest entry point.",
        }
    ]
    seen.add(args.url)

    for index, link in enumerate(parser.links, start=1):
        url = link["url"]
        if url in seen:
            continue
        if not is_relevant_link(link["title"], link["section"], url):
            continue
        seen.add(url)
        title = link["title"]
        category = category_for_link(title, link["section"], url)
        base_slug = slugify(title, f"source-{index}")
        short_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        sources.append(
            {
                "id": f"{base_slug}-{short_hash}",
                "title": title,
                "url": url,
                "category": category,
                "source_type": source_type_for_url(url),
                "official": is_official_natick_source(url, args.url),
                "listed_on_official_page": True,
                "retrieved_at": now.isoformat(),
                "local_path": "",
                "status": "identified",
                "notes": f"Listed under page section: {link['section']}",
            }
        )

    return {
        "meeting_id": args.meeting_id,
        "town": "Natick",
        "state": "MA",
        "official_page_url": args.url,
        "retrieved_at": now.isoformat(),
        "retrieval_date": now.date().isoformat(),
        "source_policy": "docs/official-source-policy.md",
        "sources": sources,
        "open_items": [
            "Review the manifest categories before generating article briefs.",
            "Download and parse warrant, motions, Finance Committee recommendation book, and minutes/action documents.",
            "Mark external links as official only when they are official town-linked materials or otherwise independently verified.",
        ],
    }


def write_outputs(args: argparse.Namespace, html: str, manifest: dict[str, object]) -> None:
    meeting_dir = Path(args.meeting_dir)
    sources_dir = meeting_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    (sources_dir / "official-meeting-page.html").write_text(html, encoding="utf-8")
    (meeting_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meeting-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--meeting-dir", required=True)
    parser.add_argument(
        "--html-file",
        help="Use an already archived official meeting page instead of fetching the URL.",
    )
    args = parser.parse_args()

    try:
        if args.html_file:
            html = Path(args.html_file).read_text(encoding="utf-8")
        else:
            html = fetch_text(args.url)
        manifest = build_manifest(args, html)
        write_outputs(args, html, manifest)
    except Exception as exc:  # noqa: BLE001 - command-line tool should report all failures.
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {Path(args.meeting_dir) / 'manifest.json'}")
    print(f"Archived {Path(args.meeting_dir) / 'sources' / 'official-meeting-page.html'}")
    print(f"Sources identified: {len(manifest['sources'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
