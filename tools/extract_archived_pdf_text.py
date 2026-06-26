#!/usr/bin/env python3
"""Extract text from archived PDF sources listed in a meeting manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or fallback


def should_extract(source: dict[str, object], categories: set[str]) -> bool:
    if categories and source["category"] not in categories:
        return False
    local_path = str(source.get("local_path") or "")
    if not local_path.casefold().endswith(".pdf"):
        return False
    return bool(local_path)


def extract_pdf_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(path)
    chunks: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.append(f"\n\n--- Page {index} ---\n\n{text.strip()}")
    return "".join(chunks).strip() + "\n", len(reader.pages)


def extract_sources(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    meeting_dir = manifest_path.parent
    output_dir = meeting_dir / "working" / "extracted-text"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    categories = set(args.categories or [])
    extracted = 0

    for source in manifest["sources"]:
        if not should_extract(source, categories):
            continue
        source_path = meeting_dir / str(source["local_path"])
        if not source_path.exists():
            print(f"missing local source: {source_path}", file=sys.stderr)
            continue
        text, page_count = extract_pdf_text(source_path)
        output_name = f"{slugify(str(source['title']), str(source['id']))}.txt"
        output_path = output_dir / output_name
        output_path.write_text(text, encoding="utf-8")
        source["text_path"] = output_path.relative_to(meeting_dir).as_posix()
        source["page_count"] = page_count
        source["status"] = "parsed"
        extracted += 1
        print(f"Extracted {source['title']} ({page_count} pages) -> {source['text_path']}")

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Extracted PDFs: {extracted}")
    print(f"Updated {manifest_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--categories", nargs="*", default=[])
    args = parser.parse_args()

    try:
        return extract_sources(args)
    except Exception as exc:  # noqa: BLE001 - command-line tool should report all failures.
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
