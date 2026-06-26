#!/usr/bin/env python3
"""Generate draft Markdown article briefs from parsed warrant data."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FOR_PATTERNS = (
    "support",
    "supported",
    "valuable",
    "reasonable",
    "benefit",
    "favorable",
    "important",
    "needed",
    "necessary",
)


AGAINST_PATTERNS = (
    "concern",
    "concerns",
    "dissatisfaction",
    "opposed",
    "opposition",
    "difficult",
    "not",
    "against",
    "unsure",
    "incomplete",
)


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or fallback


def sentence_summary(article: dict[str, object]) -> str:
    title = str(article["title"])
    sponsor = str(article.get("sponsor") or "the listed sponsor")
    warrant_text = str(article.get("warrant_text") or "")
    if warrant_text:
        return f"Article {article['article']} asks Town Meeting to act on `{title}`, sponsored by {sponsor}. The official warrant text should be reviewed before this summary is finalized."
    return f"Article {article['article']} concerns `{title}`, sponsored by {sponsor}. The warrant text needs reviewer confirmation."


def consent_assessment(
    article_id: str,
    article_sources: list[dict[str, object]],
    fincom: dict[str, object] | None,
) -> tuple[str, str, str]:
    if fincom and article_id in set(fincom.get("consent_agenda_articles", [])):
        return (
            "good candidate",
            "The article appears in the official consent agenda motion parsed from the Finance Committee recommendation book.",
            "Confirm against the final moderator consent agenda motion and remove if any Town Meeting member objects.",
        )
    has_motion = any(source["category"] == "motion_or_amendment" for source in article_sources)
    has_presentation = any(source["category"] == "presentation" for source in article_sources)
    if fincom:
        if has_motion:
            return (
                "not recommended",
                "The article was not listed in the parsed official consent agenda and has article-specific motion or amendment materials identified.",
                "Review all motions and amendments before floor action.",
            )
        return (
            "not recommended",
            "The article was not listed in the parsed official consent agenda from the Finance Committee recommendation book.",
            "This is a conservative recommendation pending final moderator review.",
        )
    if has_motion:
        return (
            "needs review",
            "Article-specific motions or amendments are already identified, so consent suitability should wait for motion and FinCom review.",
            "Check whether the official consent agenda motion includes or excludes this article.",
        )
    if has_presentation:
        return (
            "needs review",
            "A sponsor presentation is identified, which may indicate floor discussion or complexity.",
            "Review the presentation and Finance Committee discussion before treating this as consent-ready.",
        )
    return (
        "needs review",
        "The warrant article has been parsed, but Finance Committee recommendation, motions, and official consent agenda materials have not yet been merged.",
        "Do not place on a consent agenda solely from this draft brief.",
    )


def excerpt(value: str, limit: int = 900) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value or "Needs parsing from the official Finance Committee recommendation book."
    return value[: limit - 3].rsplit(" ", 1)[0] + "..."


def sentences(value: str) -> list[str]:
    compacted = re.sub(r"\s+", " ", value).strip()
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compacted) if part.strip()]


def discussion_points(discussion: str, patterns: tuple[str, ...]) -> list[str]:
    points = []
    for sentence in sentences(discussion):
        lowered = sentence.casefold()
        if any(pattern in lowered for pattern in patterns):
            points.append(sentence)
        if len(points) == 3:
            break
    return points


def bullet_points(points: list[str], fallback: str) -> str:
    if not points:
        return fallback
    return "\n".join(f"- {point}" for point in points)


def finance_section(article_id: str, fincom_by_article: dict[str, dict[str, object]], fincom_warnings: list[str]) -> str:
    if fincom_warnings:
        warnings = "\n".join(f"- {warning}" for warning in fincom_warnings)
        return f"""Recommendation: Not merged.
Vote: Not merged.
Unanimous: Not merged.

Source Warning:

{warnings}

Discussion Highlights:

The Finance Committee source file has a meeting mismatch warning, so recommendation content was not merged into this brief.

Arguments For:

Needs a corrected official Finance Committee recommendation source.

Arguments Against:

Needs a corrected official Finance Committee recommendation source.
"""

    fincom = fincom_by_article.get(article_id)
    if not fincom:
        return """Recommendation: Needs parsing from the official Finance Committee recommendation book.
Vote: Needs parsing.
Unanimous: Needs parsing.

Discussion Highlights:

Needs parsing from the official Finance Committee recommendation book.

Arguments For:

Needs parsing from official Finance Committee materials.

Arguments Against:

Needs parsing from official Finance Committee materials.
"""

    discussion = str(fincom.get("discussion") or "")
    for_points = discussion_points(discussion, FOR_PATTERNS)
    against_points = discussion_points(discussion, AGAINST_PATTERNS)
    return f"""Recommendation: {fincom.get('recommendation') or 'Needs review'}
Vote: {fincom.get('quantum_of_vote') or 'Needs review'}
Unanimous: {fincom.get('unanimity') or 'Needs review'}
Date voted: {fincom.get('date_voted') or 'Needs review'}
Motion vote threshold: {fincom.get('motion_vote_threshold') or 'Needs review'}

Discussion Highlights:

{excerpt(discussion)}

Draft Arguments For (reviewer-confirm):

{bullet_points(for_points, 'Needs reviewer summary from the official discussion text.')}

Draft Arguments Against (reviewer-confirm):

{bullet_points(against_points, 'Needs reviewer summary from the official discussion text.')}
"""


def source_rows(sources: list[dict[str, object]]) -> str:
    official_sources = [source for source in sources if source["official"]]
    if not official_sources:
        return "| None identified yet |  |  |  |  |\n"
    rows = []
    for source in official_sources:
        rows.append(
            f"| {source['id']} | {source['category']} | {source['official']} | {source['status']} | {source['url']} |"
        )
    return "\n".join(rows) + "\n"


def verification_rows(sources: list[dict[str, object]]) -> str:
    verification_sources = [source for source in sources if not source["official"]]
    if not verification_sources:
        return "None identified.\n"
    rows = [
        "| Source ID | Type | Status | URL |",
        "| --- | --- | --- | --- |",
    ]
    for source in verification_sources:
        rows.append(f"| {source['id']} | {source['category']} | {source['status']} | {source['url']} |")
    return "\n".join(rows) + "\n"


def related_rows(sources: list[dict[str, object]]) -> str:
    related = [source for source in sources if source["category"] not in {"warrant", "finance_committee"}]
    if not related:
        return "| No article-specific source identified yet |  |  |  |\n"
    rows = []
    for source in related:
        rows.append(f"| {source['title']} | {source['category']} | {source['url']} | Needs parsing |")
    return "\n".join(rows) + "\n"


def motion_rows(article_motions: list[dict[str, object]]) -> str:
    if not article_motions:
        return "| No parsed article-specific motion document |  |  |  |\n"
    rows = []
    for motion in article_motions:
        offered = motion.get("offered_by") or "Needs review"
        rows.append(
            f"| {motion['title']} | {motion['kind']} | {motion['status']} | {offered} |"
        )
    return "\n".join(rows) + "\n"


def motion_details(article_motions: list[dict[str, object]]) -> str:
    if not article_motions:
        return "No parsed article-specific motion text is available yet.\n"
    sections = []
    for motion in article_motions:
        text = excerpt(str(motion.get("motion_text") or motion.get("excerpt") or ""), 900)
        sections.append(
            f"""### {motion['title']}

Kind: `{motion['kind']}`
Status: `{motion['status']}`
Offered by: {motion.get('offered_by') or 'Needs review'}
Floor impact: {motion.get('floor_impact') or 'Needs review'}
Source: {motion['url']}

Excerpt:

{text or 'No substantive motion text extracted.'}
"""
        )
    return "\n".join(sections)


def action_rows(article_actions: list[dict[str, object]]) -> str:
    if not article_actions:
        return "| No parsed official final action |  |  |  |  |\n"
    rows = []
    for action in article_actions:
        rows.append(
            f"| {action.get('status') or 'Needs review'} | {action.get('motion_label') or 'Main/unspecified'} | {action.get('vote_threshold') or 'Needs review'} | {action.get('vote_count') or 'Needs review'} | {action.get('source_title') or action.get('source_id')} |"
        )
    return "\n".join(rows) + "\n"


def action_details(article_actions: list[dict[str, object]]) -> str:
    if not article_actions:
        return "No parsed official final action is available yet. Review archived minutes/action reports manually if needed.\n"
    lines = []
    for action in article_actions:
        lines.append(
            f"- {action.get('summary') or 'Needs review'} Source: {action.get('source_url')}"
        )
    return "\n".join(lines) + "\n"


def brief_markdown(
    meeting_id: str,
    article: dict[str, object],
    article_sources: list[dict[str, object]],
    meeting_sources: list[dict[str, object]],
    article_motions: list[dict[str, object]],
    article_actions: list[dict[str, object]],
    fincom: dict[str, object] | None,
    fincom_by_article: dict[str, dict[str, object]],
    fincom_warnings: list[str],
) -> str:
    all_sources = meeting_sources + article_sources
    article_id = str(article["article"])
    usable_fincom = fincom if not fincom_warnings else None
    consent_status, consent_reason, consent_caution = consent_assessment(article_id, article_sources, usable_fincom)
    return f"""# Article {article['article']}: {article['title']}

Meeting: `{meeting_id}`
Article: `{article['article']}`
Title: {article['title']}
Sponsor: {article.get('sponsor') or 'Needs review'}
Status: `draft`

## Official Sources

| Source ID | Type | Official | Status | URL |
| --- | --- | --- | --- | --- |
{source_rows(all_sources)}
## Sources Needing Verification

These sources are listed separately and should not support article summaries until a reviewer confirms their official status.

{verification_rows(all_sources)}
## Moderator Summary

{sentence_summary(article)}

## Warrant Text

{article.get('warrant_text') or 'Needs review.'}

## Related Motions And Amendments

| Item | Kind | Status | Offered By |
| --- | --- | --- | --- |
{motion_rows(article_motions)}
## Parsed Motion Details

{motion_details(article_motions)}
## Finance Committee

{finance_section(article_id, fincom_by_article, fincom_warnings)}
## Final Action

| Status | Motion | Vote Threshold | Vote Count | Source |
| --- | --- | --- | --- | --- |
{action_rows(article_actions)}
Action Notes:

{action_details(article_actions)}

## Consent Agenda Assessment

Recommendation: `{consent_status}`

Reason: {consent_reason}

Cautions: {consent_caution}

## Floor Management Notes

Vote threshold: Needs review.
Known procedural issues: Needs review.
Likely questions: Needs review.
Related articles: Needs review.
Suggested moderator preparation: Review the official warrant text, article-specific source list, FinCom recommendation, and any official motions before the article comes to the floor.

## Review Notes

Open items:

- Confirm extracted warrant text against the official PDF.
- Merge parsed motion text and FinCom recommendation details.
- Replace conservative consent assessment with criteria-based recommendation.

Reviewer:
Reviewed date:
"""


def sources_by_article(index: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for article in index.get("articles", []):
        result[str(article["article"])] = list(article.get("sources", []))
    return result


def meeting_level_sources(index: dict[str, object]) -> list[dict[str, object]]:
    return list(index.get("meeting_level_sources", []))


def load_fincom(path: str | None) -> tuple[dict[str, object] | None, dict[str, dict[str, object]], list[str]]:
    if not path:
        return None, {}, []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    warnings = list(data.get("warnings", []))
    if warnings:
        return data, {}, warnings
    return data, {str(article["article"]): article for article in data.get("articles", [])}, []


def load_motions(path: str | None) -> dict[str, list[dict[str, object]]]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        str(article_id): list(motions)
        for article_id, motions in data.get("by_article", {}).items()
    }


def load_actions(path: str | None) -> dict[str, list[dict[str, object]]]:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        str(article_id): list(actions)
        for article_id, actions in data.get("by_article", {}).items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warrant-articles", required=True)
    parser.add_argument("--article-source-index", required=True)
    parser.add_argument("--fincom-recommendations")
    parser.add_argument("--motions")
    parser.add_argument("--actions")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    warrant_articles = json.loads(Path(args.warrant_articles).read_text(encoding="utf-8"))
    source_index = json.loads(Path(args.article_source_index).read_text(encoding="utf-8"))
    fincom, fincom_by_article, fincom_warnings = load_fincom(args.fincom_recommendations)
    motions_by_article = load_motions(args.motions)
    actions_by_article = load_actions(args.actions)
    by_article = sources_by_article(source_index)
    meeting_sources = meeting_level_sources(source_index)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    for article in warrant_articles["articles"]:
        article_id = str(article["article"])
        filename = f"article-{article_id.zfill(2)}-{slugify(str(article['title']), 'untitled')}.md"
        output_path = output_dir / filename
        output_path.write_text(
            brief_markdown(
                str(warrant_articles["meeting_id"]),
                article,
                by_article.get(article_id, []),
                meeting_sources,
                motions_by_article.get(article_id, []),
                actions_by_article.get(article_id, []),
                fincom,
                fincom_by_article,
                fincom_warnings,
            ),
            encoding="utf-8",
        )
        generated += 1

    print(f"Generated article briefs: {generated}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
