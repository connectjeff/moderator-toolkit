#!/usr/bin/env python3
"""Parse Town Meeting action/minutes documents into article outcomes."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ARTICLE_HEADING = re.compile(r"^ARTICLE\s+([0-9]+[A-Z]?)\s*:\s*(.*)$", re.IGNORECASE)
PAGE_MARKER = re.compile(r"--- Page [0-9]+ ---")
OUTCOME_TERMS = (
    "passed",
    "failed",
    "defeated",
    "referred",
    "refer back",
    "postpone",
    "postponed",
    "no action",
)


def compact(value: str) -> str:
    value = value.replace("\ufb01", "fi").replace("\ufb00", "ff").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip()


def normalize_text(value: str) -> str:
    value = PAGE_MARKER.sub("", value)
    value = re.sub(r"passe\s+d", "passed", value, flags=re.IGNORECASE)
    value = re.sub(r"Move\s+d", "Moved", value, flags=re.IGNORECASE)
    return value


def article_sort_key(article_id: str) -> tuple[int, str]:
    match = re.fullmatch(r"([0-9]+)([a-z]?)", article_id.casefold())
    if not match:
        return (9999, article_id)
    return (int(match.group(1)), match.group(2))


def split_sentences(text: str) -> list[str]:
    compacted = compact(text)
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compacted) if part.strip()]


def outcome_status(text: str) -> str:
    lowered = text.casefold()
    if "failed" in lowered or "defeated" in lowered:
        return "failed"
    if "no action" in lowered and "passes" in lowered:
        return "no action passed"
    if "refer" in lowered and "passed" in lowered:
        return "referred"
    if "postpone" in lowered and "passed" in lowered:
        return "postponed"
    if "passed" in lowered or "passes" in lowered:
        return "passed"
    if "refer" in lowered:
        return "refer motion"
    if "postpone" in lowered:
        return "postpone motion"
    if "no action" in lowered:
        return "no action"
    return "needs review"


def vote_count(text: str) -> str:
    match = re.search(r"\(([\d\s]+\s*/\s*[\d\s]+\s*/\s*[\d\s]+)\)", text)
    return re.sub(r"\s+", "", match.group(1)) if match else ""


def vote_threshold(text: str) -> str:
    lowered = text.casefold()
    if "4/5" in lowered or "4/5ths" in lowered:
        return "4/5"
    if "2/3" in lowered or "2/3rds" in lowered:
        return "2/3"
    if "majority" in lowered:
        return "majority"
    if "unanimously" in lowered:
        return "unanimous"
    return ""


def motion_label(text: str) -> str:
    patterns = [
        r"\bmotion to refer\b",
        r"\brefer back\b",
        r"\bMotion\s+([A-Z])\b",
        r"\bMotion\s+([A-Z])\s+under\b",
        r"\bpositive main motion\b",
        r"\bmain motion\b",
        r"\bconsent agenda\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        if match.groups():
            return f"Motion {match.group(1).upper()}"
        label = compact(match.group(0)).title()
        if "Refer" in label:
            return "Refer"
        return label
    return ""


def source_is_usable_action_source(source: dict[str, object]) -> bool:
    return bool(source.get("official") or source.get("accepted_unofficial"))


def source_provenance(source: dict[str, object]) -> str:
    if source.get("official"):
        return "official"
    if source.get("accepted_unofficial"):
        return "accepted_unofficial"
    return "unverified"


def status_from_vote_result(result: str) -> str:
    lowered = result.casefold()
    if "failed" in lowered:
        return "failed"
    if "refer" in lowered:
        return "referred"
    if "favorable" in lowered:
        return "passed"
    if result.strip():
        return "needs review"
    return "vote count only"


def article_ids_from_sentence(sentence: str, current_article: str | None) -> list[str]:
    ids = {match.group(1).upper() for match in re.finditer(r"\bArticle\s+([0-9]+[A-Z]?)\b", sentence, re.IGNORECASE)}
    if not ids and current_article:
        ids.add(current_article)
    return sorted(ids, key=article_sort_key)


def parse_consent_outcomes(text: str, source: dict[str, object]) -> list[dict[str, object]]:
    outcomes = []
    match = re.search(
        r"Articles\s+([0-9A-Z,\sand]+?)\s+out of order and that they be\s+[\"“ ]*Passed by Consent",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return outcomes
    article_text = compact(match.group(1)).replace(" and ", ", ")
    article_ids = [
        part.strip().upper()
        for part in article_text.split(",")
        if re.fullmatch(r"[0-9]+[A-Z]?", part.strip(), re.IGNORECASE)
    ]
    vote_sentence = ""
    for sentence in split_sentences(text):
        if "consent agenda passed" in sentence.casefold():
            vote_sentence = sentence
            break
    for article_id in article_ids:
        outcomes.append(
            {
                "article": article_id,
                "status": "passed by consent",
                "motion_label": "Consent Agenda",
                "vote_threshold": vote_threshold(vote_sentence) or "majority",
                "vote_count": vote_count(vote_sentence),
                "summary": vote_sentence or "Article listed in official consent agenda motion passed by consent.",
                "source_id": source["id"],
                "source_title": source["title"],
                "source_url": source["url"],
                "source_text_path": source.get("text_path", ""),
            }
        )
    return outcomes


def article_sections(lines: list[str]) -> list[tuple[str, str, str]]:
    headings: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = ARTICLE_HEADING.match(compact(line))
        if match:
            headings.append((index, match.group(1).upper(), compact(match.group(2))))
    sections: list[tuple[str, str, str]] = []
    for position, (start, article_id, title) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        sections.append((article_id, title, "\n".join(lines[start + 1 : end])))
    return sections


def parse_article_outcomes(text: str, source: dict[str, object]) -> list[dict[str, object]]:
    outcomes: list[dict[str, object]] = []
    lines = text.splitlines()
    for article_id, title, body in article_sections(lines):
        for sentence in split_sentences(body):
            lowered = sentence.casefold()
            if not any(term in lowered for term in OUTCOME_TERMS):
                continue
            if "finance committee" in lowered or "recommendation" in lowered:
                continue
            for extracted_id in article_ids_from_sentence(sentence, article_id):
                outcomes.append(
                    {
                        "article": extracted_id,
                        "status": outcome_status(sentence),
                        "motion_label": motion_label(sentence),
                        "vote_threshold": vote_threshold(sentence),
                        "vote_count": vote_count(sentence),
                        "summary": sentence,
                        "source_id": source["id"],
                        "source_title": source["title"],
                        "source_url": source["url"],
                        "source_text_path": source.get("text_path", ""),
                        "section_title": title,
                    }
                )
    return outcomes


def parse_source(source: dict[str, object], meeting_dir: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    title = str(source.get("title", ""))
    local_path = str(source.get("local_path") or "")
    if local_path.casefold().endswith(".csv"):
        return parse_csv_vote_source(source, meeting_dir)
    if "session" not in title.casefold():
        return [], {
            "source_id": source["id"],
            "title": source["title"],
            "status": "archived_not_action_minutes",
            "outcome_count": 0,
        }
    text_path = source.get("text_path")
    if not text_path:
        return [], {
            "source_id": source["id"],
            "title": source["title"],
            "status": "not_extracted",
            "outcome_count": 0,
        }
    raw_text = (meeting_dir / str(text_path)).read_text(encoding="utf-8")
    text = normalize_text(raw_text)
    outcomes = parse_consent_outcomes(text, source) + parse_article_outcomes(text, source)
    source_status = "parsed" if outcomes else "no_article_outcomes_found"
    return outcomes, {
        "source_id": source["id"],
        "title": source["title"],
        "status": source_status,
        "outcome_count": len(outcomes),
        "text_path": text_path,
    }


def parse_csv_vote_source(source: dict[str, object], meeting_dir: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    local_path = source.get("local_path")
    if not local_path:
        return [], {
            "source_id": source["id"],
            "title": source["title"],
            "status": "not_archived",
            "outcome_count": 0,
        }
    source_path = meeting_dir / str(local_path)
    with source_path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    outcomes = []
    for row in rows:
        article_id = compact(row.get("Article #", ""))
        if not re.fullmatch(r"[0-9]+[A-Z]?", article_id, re.IGNORECASE):
            continue
        vote_count_text = compact(row.get("TM Vote (UNOFFICIAL)", ""))
        result_text = compact(row.get("", ""))
        summary = f"Unofficial TM vote: {vote_count_text}"
        if result_text:
            summary = f"{summary}; result note: {result_text}"
        outcomes.append(
            {
                "article": article_id.upper(),
                "status": status_from_vote_result(result_text),
                "motion_label": "Vote result",
                "vote_threshold": "",
                "vote_count": vote_count_text,
                "summary": summary,
                "source_id": source["id"],
                "source_title": source["title"],
                "source_url": source["url"],
                "source_text_path": local_path,
                "source_provenance": source_provenance(source),
                "source_note": source.get("acceptance_basis") or source.get("notes", ""),
            }
        )

    return outcomes, {
        "source_id": source["id"],
        "title": source["title"],
        "status": "parsed" if outcomes else "no_article_outcomes_found",
        "outcome_count": len(outcomes),
        "text_path": local_path,
        "source_provenance": source_provenance(source),
    }


def parse_actions(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    meeting_dir = manifest_path.parent
    outcomes: list[dict[str, object]] = []
    source_summaries = []
    for source in manifest["sources"]:
        if source.get("category") != "minutes_or_actions" or not source_is_usable_action_source(source):
            continue
        parsed_outcomes, summary = parse_source(source, meeting_dir)
        outcomes.extend(parsed_outcomes)
        source_summaries.append(summary)

    by_article: dict[str, list[dict[str, object]]] = {}
    for outcome in outcomes:
        by_article.setdefault(str(outcome["article"]), []).append(outcome)

    return {
        "meeting_id": manifest["meeting_id"],
        "outcome_count": len(outcomes),
        "article_count_with_outcomes": len(by_article),
        "outcomes": outcomes,
        "by_article": by_article,
        "source_summaries": source_summaries,
        "open_items": [
            "Outcome parsing is conservative and should be reviewed against source materials.",
            "Accepted unofficial vote-result sources must be labeled and should not be described as official final actions.",
            "Raw voting-system reports are archived but may not produce article outcomes without prose result text.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    parsed = parse_actions(Path(args.manifest))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Outcomes parsed: {parsed['outcome_count']}")
    print(f"Articles with outcomes: {parsed['article_count_with_outcomes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
