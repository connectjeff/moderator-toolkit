#!/usr/bin/env python3
"""Download selected official sources from a meeting manifest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/html": ".html",
}


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or fallback


def extension_for(url: str, content_type: str) -> str:
    path = urllib.parse.urlparse(url).path
    suffix = Path(path).suffix
    if suffix:
        return suffix
    normalized_content_type = content_type.split(";", 1)[0].strip().casefold()
    if normalized_content_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[normalized_content_type]
    guessed = mimetypes.guess_extension(normalized_content_type)
    return guessed or ".bin"


def fetch_bytes(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "TownModeratorToolkit/0.1 (+official-source-archive)",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.headers.get("Content-Type", "")


def should_archive(source: dict[str, object], categories: set[str], official_only: bool) -> bool:
    if categories and source["category"] not in categories:
        return False
    if official_only and not source["official"]:
        return False
    if source["category"] == "meeting_page":
        return False
    return True


def archive_sources(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    meeting_dir = manifest_path.parent
    sources_dir = meeting_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    categories = set(args.categories or [])
    archived = 0
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    for source in manifest["sources"]:
        if archived >= args.limit:
            break
        if not should_archive(source, categories, args.official_only):
            continue
        if source.get("local_path"):
            continue

        body, content_type = fetch_bytes(str(source["url"]))
        digest = hashlib.sha256(body).hexdigest()
        ext = extension_for(str(source["url"]), content_type)
        filename = f"{slugify(str(source['title']), str(source['id']))}-{digest[:8]}{ext}"
        relative_path = Path("sources") / filename
        output_path = meeting_dir / relative_path
        output_path.write_bytes(body)

        source["local_path"] = relative_path.as_posix()
        source["status"] = "archived"
        source["archived_at"] = now
        source["sha256"] = digest
        source["bytes"] = len(body)
        source["content_type"] = content_type
        archived += 1
        print(f"Archived {source['title']} -> {relative_path}")

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Archived sources: {archived}")
    print(f"Updated {manifest_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--categories", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=999)
    parser.add_argument("--official-only", action="store_true")
    args = parser.parse_args()

    try:
        return archive_sources(args)
    except Exception as exc:  # noqa: BLE001 - command-line tool should report all failures.
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
