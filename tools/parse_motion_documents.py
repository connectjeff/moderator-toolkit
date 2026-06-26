#!/usr/bin/env python3
"""Parse archived motion and amendment source text from a meeting manifest."""

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
PAGE_MARKER = re.compile(r"--- Page [0-9]+ ---")


def compact(value: str) -> str:
    value = value.replace("\ufb01", "fi").replace("\ufb00", "ff").replace("\u00a0", " ")
    value = value.replace("\t", " ")
    return re.sub(r"\s+", " ", value).strip()


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


def motion_kind(title: str, text: str) -> str:
    lowered = f"{title} {text[:500]}".casefold()
    if "consent agenda" in lowered:
        return "consent_agenda"
    if "procedural motion" in lowered:
        return "procedural_motion"
    if "substitute motion" in lowered:
        return "substitute_motion"
    if "amendment" in lowered or "amend the main motion" in lowered:
        return "amendment"
    if "handout" in lowered:
        return "handout"
    if "memo" in lowered:
        return "memo"
    if "motion" in lowered or "move that" in lowered or "move to" in lowered:
        return "motion"
    return "document"


def is_blank_motion_form(text: str) -> bool:
    lowered = text.casefold()
    normalized = compact(lowered)
    if "natick town meeting motion form" not in normalized:
        return False
    if "signature" not in normalized or "vote declared by" not in normalized:
        return False
    motion_match = re.search(r"move that the town vote to\s*(.*?)\s*signature", lowered, re.DOTALL)
    return bool(motion_match and not compact(motion_match.group(1)))


def extract_offered_by(text: str) -> str:
    lines = [compact(line) for line in text.splitlines() if compact(line)]
    for line in lines:
        from_match = re.match(r"From:\s*(.+)", line, re.IGNORECASE)
        if from_match:
            return compact(from_match.group(1))
        offered_match = re.search(r"Offered by ([^,]+(?:,\s*Precinct\s*[0-9]+)?)", line, re.IGNORECASE)
        if offered_match:
            return compact(offered_match.group(1))
        member_match = re.search(r"\bI\s+([A-Z][A-Za-z .'-]+)\s+of Precinct\s*([0-9]+)\b", line)
        if member_match:
            return compact(f"{member_match.group(1)}, Precinct {member_match.group(2)}")
    patterns = [
        r"I\s+([A-Z][A-Za-z .'-]+)\s+of Precinct\s*([0-9]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        if len(match.groups()) == 2 and pattern.startswith("I"):
            return compact(f"{match.group(1)}, Precinct {match.group(2)}")
        return compact(match.group(1))
    return ""


def extract_motion_text(text: str) -> str:
    cleaned = PAGE_MARKER.sub("", text)
    cleaned = compact(cleaned)
    if is_blank_motion_form(cleaned):
        return ""
    motion_starts = [
        r"\bMove that\b",
        r"\bMOVE that\b",
        r"\bMove to\b",
        r"\bMOVE to\b",
        r"\bI move that\b",
    ]
    starts = [match.start() for pattern in motion_starts for match in re.finditer(pattern, cleaned, re.IGNORECASE)]
    if not starts:
        return cleaned
    return cleaned[min(starts) :]


def has_extractable_text(text: str) -> bool:
    cleaned = PAGE_MARKER.sub("", text)
    cleaned = compact(cleaned)
    return bool(cleaned)


def floor_impact(kind: str, status: str) -> str:
    if status == "blank_template":
        return "No substantive motion text extracted; verify whether the official link points to the intended motion."
    if status == "no_extractable_text":
        return "PDF text extraction produced no substantive text; OCR or manual review is needed."
    if kind == "consent_agenda":
        return "Potentially controls consent agenda handling or article order."
    if kind == "procedural_motion":
        return "Procedural effect; moderator should review timing, order, and whether debate or vote thresholds apply."
    if kind == "substitute_motion":
        return "May replace the main motion; moderator should review precedence, scope, and text before the article is called."
    if kind == "amendment":
        return "May amend the main motion; moderator should review scope and order of consideration."
    if kind == "motion":
        return "Likely article motion text; compare with warrant and FinCom motion before floor action."
    if kind in {"memo", "handout"}:
        return "Supporting material; review for article context but do not treat as motion text without confirmation."
    return "Needs moderator review."


def parse_source(source: dict[str, object], meeting_dir: Path) -> dict[str, object] | None:
    text_path = source.get("text_path")
    if not text_path:
        return None
    raw_text = (meeting_dir / str(text_path)).read_text(encoding="utf-8")
    motion_text = extract_motion_text(raw_text)
    kind = motion_kind(str(source["title"]), motion_text or raw_text)
    if is_blank_motion_form(raw_text):
        status = "blank_template"
    elif not has_extractable_text(raw_text):
        status = "no_extractable_text"
    else:
        status = "parsed"
    article_ids = article_ids_from_title(str(source["title"]))
    return {
        "source_id": source["id"],
        "title": source["title"],
        "url": source["url"],
        "local_path": source.get("local_path", ""),
        "text_path": text_path,
        "article_ids": article_ids,
        "kind": kind,
        "status": status,
        "offered_by": extract_offered_by(raw_text),
        "motion_text": motion_text,
        "excerpt": compact(motion_text or raw_text)[:1200],
        "floor_impact": floor_impact(kind, status),
        "open_items": [
            "Confirm parsed motion text against the official PDF.",
            "Determine precedence, scope, and vote threshold before floor use.",
        ],
    }


def parse_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    meeting_dir = manifest_path.parent
    motions = []
    for source in manifest["sources"]:
        if source.get("category") != "motion_or_amendment" or not source.get("official"):
            continue
        parsed = parse_source(source, meeting_dir)
        if parsed:
            motions.append(parsed)

    by_article: dict[str, list[dict[str, object]]] = {}
    meeting_level = []
    for motion in motions:
        article_ids = motion["article_ids"]
        if not article_ids:
            meeting_level.append(motion)
            continue
        for article_id in article_ids:
            by_article.setdefault(article_id, []).append(motion)

    return {
        "meeting_id": manifest["meeting_id"],
        "motion_count": len(motions),
        "article_count_with_motions": len(by_article),
        "motions": motions,
        "by_article": by_article,
        "meeting_level_motions": meeting_level,
        "open_items": [
            "Parser is intentionally conservative and does not decide procedural validity.",
            "Review blank-template and supporting-material records before relying on them.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    parsed = parse_manifest(Path(args.manifest))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Motions parsed: {parsed['motion_count']}")
    print(f"Articles with motion sources: {parsed['article_count_with_motions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
