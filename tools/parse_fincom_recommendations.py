#!/usr/bin/env python3
"""Parse Finance Committee recommendation sections from extracted book text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ARTICLE_HEADING = re.compile(r"^Article\s+([0-9]+[A-Z]?)\s*$", re.IGNORECASE)
ARTICLE_LANGUAGE_LABEL = "ARTICLE LANGUAGE"
PURPOSE_LABEL = "PURPOSE OF THE ARTICLE"
RECOMMENDATION_LABEL = "FINANCE COMMITTEE RECOMMENDATION"
DISCUSSION_LABEL = "FINANCE COMMITTEE PUBLIC HEARING AND DISCUSSION"
PAGE_MARKER = re.compile(r"--- Page [0-9]+ ---")


def normalize_text(text: str) -> str:
    replacements = {
        "\ufb01": "fi",
        "\ufb00": "ff",
        "\u00a0": " ",
        "Fiscal Y ear": "Fiscal Year",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = PAGE_MARKER.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_between(text: str, start_label: str, end_labels: list[str]) -> str:
    start = text.find(start_label)
    if start < 0:
        return ""
    start += len(start_label)
    end_positions = [text.find(label, start) for label in end_labels]
    end_positions = [position for position in end_positions if position >= 0]
    end = min(end_positions) if end_positions else len(text)
    return compact(text[start:end])


def extract_line_value(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*:\s*(.+)", text, re.IGNORECASE)
    return compact(match.group(1)) if match else ""


def extract_motion(text: str) -> tuple[str, str]:
    match = re.search(
        r"(?P<label>MOTIONS?|Motion|MOTION(?:\s+[A-Z])?)\s*(?:\((?P<threshold>[^)]*Vote)\))?(?P<body>.*?)(?:FINANCE COMMITTEE PUBLIC HEARING AND DISCUSSION|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return "", ""
    threshold = compact(match.group("threshold") or "")
    motion_text = compact(match.group("body"))
    return threshold, motion_text


def extract_title_and_sponsor(body: str) -> tuple[str, str]:
    before_language = body.split(ARTICLE_LANGUAGE_LABEL, 1)[0]
    lines = [compact(line) for line in before_language.splitlines() if compact(line)]
    title_lines: list[str] = []
    sponsor = ""
    for line in lines:
        sponsor_match = re.fullmatch(r"\(([^()]*)\)", line)
        if sponsor_match:
            sponsor = sponsor_match.group(1)
            break
        if not re.fullmatch(r"[0-9]+", line):
            title_lines.append(line)
    return compact(" ".join(title_lines)), sponsor


def recommendation_status(value: str) -> str:
    normalized = value.casefold()
    if "no recommendation" in normalized:
        return "no recommendation"
    if "unfavorable" in normalized:
        return "unfavorable"
    if "favorable" in normalized:
        return "favorable"
    return "needs review" if not value else value


def recommendation_unanimity(quantum: str, recommendation: str) -> str:
    match = re.search(r"([0-9]+)\s*-\s*([0-9]+)\s*-\s*([0-9]+)", quantum)
    if not match:
        return "needs review"
    yes, no, abstain = (int(match.group(index)) for index in (1, 2, 3))
    if yes > 0 and no == 0 and abstain == 0 and recommendation_status(recommendation) == "favorable":
        return "unanimously favorable"
    if yes > 0 and no == 0 and recommendation_status(recommendation) == "favorable":
        return "favorable without opposition"
    return "not unanimous"


def parse_article_section(article_id: str, body: str) -> dict[str, object]:
    title, sponsor = extract_title_and_sponsor(body)
    recommendation = extract_line_value(body, "RECOMMENDATION")
    quantum = extract_line_value(body, "QUANTUM OF VOTE")
    voted_date = extract_line_value(body, "DATE VOTED")
    threshold, motion_text = extract_motion(body)
    return {
        "article": article_id.upper(),
        "title": title,
        "sponsor": sponsor,
        "article_language": extract_between(body, ARTICLE_LANGUAGE_LABEL, [PURPOSE_LABEL]),
        "purpose": extract_between(body, PURPOSE_LABEL, [RECOMMENDATION_LABEL]),
        "recommendation": recommendation,
        "recommendation_status": recommendation_status(recommendation),
        "quantum_of_vote": quantum,
        "unanimity": recommendation_unanimity(quantum, recommendation),
        "date_voted": voted_date,
        "motion_vote_threshold": threshold,
        "motion_text": motion_text,
        "discussion": extract_between(body, DISCUSSION_LABEL, []),
        "source_quality": "parsed_from_fincom_text",
        "open_items": [
            "Confirm parsed recommendation, vote quantum, motion, and discussion against the official PDF.",
        ],
    }


def title_for_mismatch_scan(text: str) -> str:
    lines = [compact(line) for line in text.splitlines() if compact(line)]
    return " ".join(lines[:8])


def expected_meeting_tokens(meeting_id: str) -> list[str]:
    tokens = []
    if "SATM" in meeting_id.upper():
        tokens.append("Spring")
    if "FATM" in meeting_id.upper():
        tokens.append("Fall")
    year_match = re.search(r"([0-9]{4})", meeting_id)
    if year_match:
        tokens.append(year_match.group(1))
    return tokens


def meeting_warnings(meeting_id: str, text: str) -> list[str]:
    header = title_for_mismatch_scan(text)
    warnings = []
    for token in expected_meeting_tokens(meeting_id):
        if token not in header:
            warnings.append(
                f"Expected meeting token `{token}` for {meeting_id} was not found in the FinCom book header: {header}"
            )
    return warnings


def parse_fincom(text: str, meeting_id: str) -> dict[str, object]:
    normalized = normalize_text(text)
    source_window = normalized
    additional_marker = "Additional Materials"
    first_article_body = source_window.find(ARTICLE_LANGUAGE_LABEL)
    additional_position = source_window.rfind(additional_marker)
    if additional_position > first_article_body >= 0:
        source_window = source_window[:additional_position]
    articles = []
    lines = source_window.splitlines()
    candidates: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = ARTICLE_HEADING.match(compact(line))
        if not match:
            continue
        lookahead = "\n".join(lines[index + 1 : index + 8])
        if ARTICLE_LANGUAGE_LABEL in lookahead:
            candidates.append((index, match.group(1).upper()))

    for position, (start, article_id) in enumerate(candidates):
        end = candidates[position + 1][0] if position + 1 < len(candidates) else len(lines)
        body = "\n".join(lines[start + 1 : end])
        body = body.split("~~ END OF ARTICLE ~~", 1)[0]
        if ARTICLE_LANGUAGE_LABEL not in body or RECOMMENDATION_LABEL not in body:
            continue
        articles.append(parse_article_section(article_id, body))
    return {
        "meeting_id": meeting_id,
        "article_count": len(articles),
        "articles": articles,
        "warnings": meeting_warnings(meeting_id, normalized),
        "open_items": [
            "Review parsed sections before using them as final moderator briefing text.",
            "Recommendation summaries are extracted from official text but are not legal or procedural advice.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meeting-id", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    parsed = parse_fincom(text, args.meeting_id)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Articles parsed: {parsed['article_count']}")
    for warning in parsed["warnings"]:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
