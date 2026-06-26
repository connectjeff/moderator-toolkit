#!/usr/bin/env python3
"""Generate moderator-facing HTML reports for meeting folders."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote


REPORT_CSS = """
:root {
  color-scheme: light;
  --bg: #f7f8f5;
  --ink: #1d2522;
  --muted: #59625e;
  --line: #cfd8d0;
  --panel: #ffffff;
  --accent: #0f766e;
  --accent-dark: #115e59;
  --warn: #9a3412;
  --soft: #e9f4f1;
  --soft-warn: #fff3e8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 15px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--accent-dark); text-decoration-thickness: 0.08em; }
header {
  padding: 32px clamp(18px, 4vw, 48px) 24px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
}
main { padding: 24px clamp(18px, 4vw, 48px) 48px; }
h1, h2, h3 { line-height: 1.15; margin: 0; }
h1 { font-size: clamp(2rem, 5vw, 3.75rem); max-width: 980px; }
h2 { font-size: 1.35rem; margin-top: 32px; margin-bottom: 12px; }
h3 { font-size: 1rem; margin-bottom: 8px; }
p { margin: 8px 0; }
.eyebrow {
  margin-bottom: 8px;
  color: var(--muted);
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-top: 16px;
  color: var(--muted);
}
.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.nav a, .pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 4px 8px;
  background: var(--panel);
  color: var(--ink);
  text-decoration: none;
  white-space: nowrap;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
}
.stat, .panel, .article {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.stat { padding: 14px; }
.stat strong { display: block; font-size: 1.8rem; line-height: 1; }
.stat span { color: var(--muted); }
.panel { padding: 16px; margin-bottom: 14px; }
.news-preview {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 18px;
  max-width: 980px;
}
.news-preview .dek {
  color: var(--muted);
  font-size: 1rem;
  font-weight: 700;
  margin: 4px 0 12px;
}
.news-preview p {
  font-size: 1.02rem;
  margin: 10px 0;
}
.article { padding: 16px; margin-bottom: 16px; }
.article-title {
  display: flex;
  gap: 12px;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
}
.article-title h3 { font-size: 1.1rem; }
.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.field {
  border-left: 3px solid var(--accent);
  padding-left: 10px;
}
.field.warning { border-color: var(--warn); background: var(--soft-warn); padding: 8px 10px; }
.field label {
  display: block;
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
}
table {
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--line);
}
th, td {
  border-bottom: 1px solid var(--line);
  padding: 8px;
  text-align: left;
  vertical-align: top;
}
th { background: var(--soft); font-size: 0.82rem; text-transform: uppercase; }
tr:last-child td { border-bottom: 0; }
.scroll { overflow-x: auto; }
.source-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 10px;
}
.source-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  padding: 12px;
}
.source-card p { color: var(--muted); font-size: 0.9rem; overflow-wrap: anywhere; }
.tag {
  display: inline-block;
  border-radius: 4px;
  padding: 2px 5px;
  background: var(--soft);
  color: var(--accent-dark);
  font-size: 0.78rem;
  font-weight: 700;
}
.tag.warn { background: var(--soft-warn); color: var(--warn); }
.trace { margin-top: 10px; font-size: 0.9rem; }
.trace ul { margin: 6px 0 0; padding-left: 18px; }
.open-items li { margin-bottom: 5px; }
footer {
  padding: 16px clamp(18px, 4vw, 48px) 32px;
  color: var(--muted);
  border-top: 1px solid var(--line);
  background: #ffffff;
}
@media print {
  body { background: #ffffff; font-size: 12px; }
  header, main, footer { padding-left: 0; padding-right: 0; }
  .nav { display: none; }
  .article, .panel, .stat { break-inside: avoid; }
}
"""


def load_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def text(value: object, fallback: str = "") -> str:
    if value is None:
        return fallback
    value_text = str(value).strip()
    return value_text or fallback


def esc(value: object) -> str:
    return html.escape(text(value))


def excerpt(value: object, limit: int = 300) -> str:
    compacted = re.sub(r"\s+", " ", text(value)).strip()
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rsplit(" ", 1)[0] + "..."


def href(path_or_url: str) -> str:
    if not path_or_url:
        return ""
    if re.match(r"^https?://", path_or_url):
        return path_or_url
    return quote(path_or_url)


def link(label: object, path_or_url: str, css_class: str = "") -> str:
    label_text = esc(label)
    if not path_or_url:
        return label_text
    class_attr = f' class="{css_class}"' if css_class else ""
    return f'<a{class_attr} href="{html.escape(href(path_or_url), quote=True)}">{label_text}</a>'


def badge(value: object, warn: bool = False) -> str:
    cls = "tag warn" if warn else "tag"
    return f'<span class="{cls}">{esc(value)}</span>'


def article_file(meeting_dir: Path, article: dict[str, object]) -> str:
    article_id = text(article.get("article"))
    pattern = f"article-{article_id.zfill(2)}-*.md"
    matches = sorted((meeting_dir / "articles").glob(pattern))
    if matches:
        return str(matches[0].relative_to(meeting_dir))
    return ""


def category_label(category: str) -> str:
    labels = {
        "finance_committee": "Finance Committee",
        "meeting_page": "Meeting Page",
        "minutes_or_actions": "Minutes And Actions",
        "motion_or_amendment": "Motions And Amendments",
        "presentation": "Presentations",
        "resource": "Resources",
        "warrant": "Warrant",
    }
    return labels.get(category, category.replace("_", " ").title())


def source_provenance(source: dict[str, object]) -> str:
    if source.get("official"):
        return "official"
    if source.get("accepted_unofficial"):
        return "accepted unofficial"
    return "needs verification"


def source_links(source: dict[str, object]) -> str:
    parts = []
    if source.get("local_path"):
        parts.append(link("local", text(source.get("local_path"))))
    if source.get("text_path"):
        parts.append(link("text", text(source.get("text_path"))))
    if source.get("url"):
        parts.append(link("source URL", text(source.get("url"))))
    return " | ".join(parts) if parts else "No link recorded"


def source_card(source: dict[str, object]) -> str:
    provenance = source_provenance(source)
    warn = provenance == "needs verification" or text(source.get("status")) in {"source_mismatch", "no_extractable_text"}
    title = text(source.get("title"), source.get("id", "Untitled source"))
    return f"""
<article class="source-card" id="source-{esc(source.get('id'))}">
  <h3>{esc(title)}</h3>
  <p>{badge(category_label(text(source.get('category'))))} {badge(provenance, warn)} {badge(source.get('status', 'status unknown'), warn)}</p>
  <p>{source_links(source)}</p>
  <p>{esc(source.get('notes', ''))}</p>
</article>
"""


def open_item_list(items: list[object]) -> str:
    if not items:
        return "<p>No open items recorded.</p>"
    return "<ul class=\"open-items\">" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def count_problem_sources(sources: list[dict[str, object]]) -> int:
    problem_statuses = {"identified", "source_mismatch", "no_extractable_text", "blank_template"}
    return sum(
        1
        for source in sources
        if text(source.get("status")) in problem_statuses
        or (not source.get("official") and not source.get("accepted_unofficial"))
    )


def article_phrase(article: dict[str, object]) -> str:
    title = clean_title(text(article.get("title"), "an article"))
    return f"Article {text(article.get('article'))}, {title}"


def clean_title(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = cleaned.replace("By law", "Bylaw").replace("Appointment s", "Appointments")
    return cleaned


def article_count_phrase(count: int) -> str:
    article = "an" if str(count).startswith(("8", "11", "18")) else "a"
    return f"{article} {count}-article warrant"


def human_join(items: list[str], limit: int = 4) -> str:
    visible = items[:limit]
    if not visible:
        return ""
    if len(visible) == 1:
        return visible[0]
    if len(visible) == 2:
        return f"{visible[0]} and {visible[1]}"
    return ", ".join(visible[:-1]) + f", and {visible[-1]}"


def article_subject_text(article: dict[str, object]) -> str:
    value = f"{article.get('title', '')} {article.get('warrant_text', '')}"
    value = re.split(r"\bY\s*ou are directed\b|\bYou are directed\b", value, maxsplit=1)[0]
    value = re.split(r"\bCertified copies of the Warrant\b", value, maxsplit=1)[0]
    return value.casefold()


def topic_buckets(articles: list[dict[str, object]]) -> dict[str, list[str]]:
    patterns = {
        "budgets and town finances": (
            "budget",
            "capital",
            "stabilization",
            "opeb",
            "unpaid bills",
            "collective bargaining",
            "revolving",
            "appropriation",
            "debt",
            "peg access",
        ),
        "zoning and land use": (
            "zoning",
            "flood",
            "accessory dwelling",
            "site plan",
            "street acceptance",
            "earth products",
            "signage",
            "district",
        ),
        "community preservation and public facilities": (
            "community preservation",
            "school",
            "memorial elementary",
            "open space",
            "historic",
            "recreation",
        ),
        "governance, bylaws, and committees": (
            "bylaw",
            "charter",
            "committee",
            "town meeting time",
            "hybrid town meeting",
            "personnel board",
            "classification",
            "select board",
        ),
        "reports, resolutions, and civic matters": (
            "report",
            "resolution",
            "resolve",
            "constitution",
            "turf",
            "moratorium",
            "employment",
            "police chief",
        ),
    }
    buckets: dict[str, list[str]] = {name: [] for name in patterns}
    for article in articles:
        haystack = article_subject_text(article)
        for name, words in patterns.items():
            if any(word in haystack for word in words):
                buckets[name].append(article_phrase(article))
                break
    return {name: values for name, values in buckets.items() if values}


def nonroutine_fincom_items(
    articles: list[dict[str, object]],
    fincom_by_article: dict[str, dict[str, object]],
) -> list[str]:
    items = []
    article_titles = {text(article.get("article")): text(article.get("title")) for article in articles}
    for article_id, fincom in fincom_by_article.items():
        recommendation = text(fincom.get("recommendation"))
        lowered = recommendation.casefold()
        if recommendation and not lowered.startswith("favorable") and lowered not in {"all favorable"}:
            title = clean_title(article_titles.get(article_id, text(fincom.get("title"), "Untitled")))
            vote = text(fincom.get("quantum_of_vote"))
            label = f"Article {article_id}, {title}, with a Finance Committee recommendation of {recommendation}"
            if vote:
                label += f" ({vote})"
            items.append(label)
    return sorted(items, key=lambda value: article_sort_key_from_phrase(value))


def article_sort_key_from_phrase(value: str) -> tuple[int, str]:
    match = re.search(r"Article\s+([0-9]+)([A-Za-z]?)", value)
    if not match:
        return (9999, value)
    return (int(match.group(1)), match.group(2).casefold())


def motion_attention_count(motions_by_article: dict[str, list[dict[str, object]]]) -> tuple[int, list[str]]:
    article_ids = []
    count = 0
    for article_id, motions in motions_by_article.items():
        noteworthy = [
            motion
            for motion in motions
            if text(motion.get("kind")) in {"procedural_motion", "substitute_motion", "amendment"}
            or text(motion.get("status")) in {"blank_template", "no_extractable_text"}
        ]
        if noteworthy:
            count += len(noteworthy)
            article_ids.append(f"Article {article_id}")
    return count, sorted(article_ids, key=article_sort_key_from_phrase)


def meeting_preview(
    meeting_id: str,
    articles: list[dict[str, object]],
    fincom_by_article: dict[str, dict[str, object]],
    motions_by_article: dict[str, list[dict[str, object]]],
    article_outcome_count: int,
) -> str:
    if not articles:
        return "<p>No parsed warrant articles are available for a meeting preview.</p>"

    article_count = len(articles)
    buckets = topic_buckets(articles)
    bucket_names = list(buckets)
    lead_topics = human_join(bucket_names, 3)
    lead = (
        f"Natick Town Meeting members will take up {article_count_phrase(article_count)} at {meeting_id}, "
        f"with business spanning {lead_topics or 'routine municipal business'}."
    )

    first_paragraph_parts = [lead]
    if "budgets and town finances" in buckets:
        first_paragraph_parts.append(
            "Fiscal matters are a central part of the warrant, including "
            f"{human_join(buckets['budgets and town finances'], 3)}."
        )
    first_paragraph = " ".join(first_paragraph_parts)

    second_sentences = []
    for topic, phrases in buckets.items():
        if topic == "budgets and town finances":
            continue
        second_sentences.append(f"The warrant also includes {topic}, led by {human_join(phrases, 3)}.")
        if len(second_sentences) == 2:
            break
    second_paragraph = " ".join(second_sentences)

    fincom_items = nonroutine_fincom_items(articles, fincom_by_article)
    motion_count, motion_articles = motion_attention_count(motions_by_article)
    third_sentences = []
    if fincom_items:
        third_sentences.append(
            "Several articles may draw extra attention because the Finance Committee did not simply recommend favorable action, including "
            f"{human_join(fincom_items, 4)}."
        )
    if motion_count:
        third_sentences.append(
            f"Moderators should also expect article-specific motion or amendment issues on {human_join(motion_articles, 5)}."
        )
    if article_outcome_count:
        third_sentences.append(
            f"The report includes parsed final-action records for {article_outcome_count} articles, making it useful for reviewing how the meeting unfolded as well as for preparation."
        )
    third_paragraph = " ".join(third_sentences)

    paragraphs = [first_paragraph]
    if second_paragraph:
        paragraphs.append(second_paragraph)
    if third_paragraph:
        paragraphs.append(third_paragraph)
    return "\n".join(f"<p>{esc(paragraph)}</p>" for paragraph in paragraphs)


def recommendation_label(fincom: dict[str, object] | None) -> str:
    if not fincom:
        return "Not parsed"
    rec = text(fincom.get("recommendation"), "Needs review")
    vote = text(fincom.get("quantum_of_vote"))
    return f"{rec} ({vote})" if vote else rec


def action_label(actions: list[dict[str, object]]) -> str:
    if not actions:
        return "No parsed final action"
    primary = actions[0]
    status = text(primary.get("status"), "Needs review")
    vote = text(primary.get("vote_count"))
    return f"{status} ({vote})" if vote else status


def motion_label(motions: list[dict[str, object]]) -> str:
    if not motions:
        return "No parsed article motion"
    substantive = [motion for motion in motions if text(motion.get("status")) not in {"blank_template", "no_extractable_text"}]
    base = substantive or motions
    kinds = Counter(text(motion.get("kind"), "motion") for motion in base)
    return ", ".join(f"{count} {kind.replace('_', ' ')}" for kind, count in sorted(kinds.items()))


def unique_items(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        compact = re.sub(r"\s+", " ", item).strip()
        if compact and compact not in seen:
            seen.add(compact)
            result.append(compact)
    return result


def floor_attention_items(
    fincom: dict[str, object] | None,
    motions: list[dict[str, object]],
    actions: list[dict[str, object]],
    meeting_has_actions: bool,
) -> list[str]:
    items = []
    if fincom:
        recommendation = text(fincom.get("recommendation")).casefold()
        if recommendation and not recommendation.startswith("favorable") and recommendation not in {"all favorable"}:
            items.append(f"Finance Committee posture is {text(fincom.get('recommendation'))}; confirm how this affects the motion expected on the floor.")
        threshold = text(fincom.get("motion_vote_threshold"))
        if threshold and threshold.casefold() not in {"requires a majority vote", "majority vote"}:
            items.append(f"Vote threshold may require attention: {threshold}.")

    for motion in motions:
        kind = text(motion.get("kind"), "motion")
        status = text(motion.get("status"))
        title = text(motion.get("title"), "Article-specific motion")
        if kind in {"procedural_motion", "substitute_motion", "amendment"}:
            motion_kind = kind.replace("_", " ")
            article = "an" if motion_kind[0] in "aeiou" else "a"
            items.append(f"{title} is {article} {motion_kind}; confirm precedence, scope, and vote threshold before floor use.")
        if status in {"blank_template", "no_extractable_text"}:
            items.append(f"{title} has status {status}; review the source before relying on it.")
        impact = text(motion.get("floor_impact"))
        if impact and "Needs review" not in impact and "Confirm" not in impact:
            items.append(f"{title}: {impact}")

    if actions:
        for action in actions:
            status = text(action.get("status")).casefold()
            if any(term in status for term in ("referred", "postpon", "reconsider", "failed", "withdraw")):
                items.append(f"Final action record may affect retrospective review: {text(action.get('summary'), text(action.get('status')))}")
    elif meeting_has_actions:
        items.append("Other articles in this meeting have parsed final actions, but this article does not.")

    return unique_items(items)


def article_trace(
    article_sources: list[dict[str, object]],
    motions: list[dict[str, object]],
) -> str:
    seen: dict[str, dict[str, object]] = {}
    for source in article_sources:
        seen[text(source.get("id"))] = source
    for motion in motions:
        if motion.get("source_id") and text(motion.get("source_id")) not in seen:
            seen[text(motion.get("source_id"))] = {
                "id": motion.get("source_id"),
                "title": motion.get("title"),
                "url": motion.get("url"),
                "category": "motion_or_amendment",
                "status": motion.get("status"),
                "official": True,
            }
    if not seen:
        return "<p>No article-specific source trace recorded.</p>"
    items = []
    for source in sorted(seen.values(), key=lambda item: (text(item.get("category")), text(item.get("title")))):
        title = text(source.get("title"), source.get("id", "source"))
        target = text(source.get("local_path")) or text(source.get("url"))
        items.append(
            f"<li>{link(title, target)} "
            f"{badge(category_label(text(source.get('category'))))} "
            f"{badge(source_provenance(source), source_provenance(source) == 'needs verification')}</li>"
        )
    return "<ul>" + "".join(items) + "</ul>"


def article_section(
    meeting_dir: Path,
    article: dict[str, object],
    article_sources: list[dict[str, object]],
    fincom: dict[str, object] | None,
    motions: list[dict[str, object]],
    actions: list[dict[str, object]],
    meeting_has_actions: bool,
) -> str:
    article_id = text(article.get("article"))
    brief_path = article_file(meeting_dir, article)
    article_attention_items = floor_attention_items(fincom, motions, actions, meeting_has_actions)
    motion_summary = motion_label(motions)
    attention_section = ""
    if article_attention_items:
        attention_section = f"""
  <details>
    <summary>Floor attention notes</summary>
    {open_item_list(article_attention_items)}
  </details>"""
    return f"""
<article class="article" id="article-{esc(article_id)}">
  <div class="article-title">
    <h3>{link(f"Article {article_id}: {text(article.get('title'), 'Untitled')}", brief_path)}</h3>
    <span>{badge(text(article.get('status'), 'draft'))}</span>
  </div>
  <div class="summary">
    <div class="field"><label>Sponsor</label>{esc(article.get('sponsor', 'Needs review'))}</div>
    <div class="field"><label>Finance Committee</label>{esc(recommendation_label(fincom))}</div>
    <div class="field"><label>Motions</label>{esc(motion_summary)}</div>
    <div class="field"><label>Final Action</label>{esc(action_label(actions))}</div>
  </div>
  <p><strong>Warrant request:</strong> {esc(excerpt(article.get('warrant_text'), 500))}</p>
  <div class="trace"><strong>Article-specific traceability:</strong>{article_trace(article_sources, motions)}</div>
{attention_section}
</article>
"""


def dashboard_rows(
    meeting_dir: Path,
    articles: list[dict[str, object]],
    fincom_by_article: dict[str, dict[str, object]],
    motions_by_article: dict[str, list[dict[str, object]]],
    actions_by_article: dict[str, list[dict[str, object]]],
) -> str:
    rows = []
    for article in articles:
        article_id = text(article.get("article"))
        brief_path = article_file(meeting_dir, article)
        rows.append(
            "<tr>"
            f"<td>{link(article_id, brief_path)}</td>"
            f"<td>{esc(article.get('title'))}</td>"
            f"<td>{esc(article.get('sponsor', 'Needs review'))}</td>"
            f"<td>{esc(recommendation_label(fincom_by_article.get(article_id)))}</td>"
            f"<td>{esc(motion_label(motions_by_article.get(article_id, [])))}</td>"
            f"<td>{esc(action_label(actions_by_article.get(article_id, [])))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def generate_report(meeting_dir: Path) -> Path:
    manifest = load_json(meeting_dir / "manifest.json", {})
    warrant = load_json(meeting_dir / "working" / "warrant-articles.json", {"articles": []})
    fincom = load_json(meeting_dir / "working" / "fincom-recommendations.json", {"articles": [], "warnings": []})
    motions = load_json(meeting_dir / "working" / "motions.json", {"by_article": {}, "motions": []})
    actions = load_json(meeting_dir / "working" / "actions.json", {"by_article": {}, "outcomes": []})
    source_index = load_json(meeting_dir / "working" / "article-source-index.json", {"articles": [], "meeting_level_sources": []})

    sources = list(manifest.get("sources", []))
    articles = list(warrant.get("articles", []))
    fincom_by_article = {text(article.get("article")): article for article in fincom.get("articles", [])}
    motions_by_article = {str(key): list(value) for key, value in motions.get("by_article", {}).items()}
    actions_by_article = {str(key): list(value) for key, value in actions.get("by_article", {}).items()}
    article_sources = {
        text(article.get("article")): list(article.get("sources", []))
        for article in source_index.get("articles", [])
    }
    source_categories = defaultdict(list)
    for source in sources:
        source_categories[text(source.get("category"), "uncategorized")].append(source)

    official_count = sum(1 for source in sources if source.get("official"))
    accepted_count = sum(1 for source in sources if source.get("accepted_unofficial"))
    parsed_count = sum(1 for source in sources if text(source.get("status")) == "parsed")
    problem_count = count_problem_sources(sources)
    article_count = len(articles)
    fincom_count = len(fincom_by_article)
    motion_count = int(motions.get("motion_count", len(motions.get("motions", []))))
    outcome_count = int(actions.get("outcome_count", len(actions.get("outcomes", []))))
    article_outcome_count = len(actions_by_article)

    manifest_open = list(manifest.get("open_items", []))
    combined_open = []
    for dataset in (warrant, fincom, motions, actions, source_index):
        combined_open.extend(dataset.get("open_items", []))
    if fincom.get("warnings"):
        combined_open.extend(fincom.get("warnings", []))

    source_sections = []
    for category in sorted(source_categories):
        cards = "".join(source_card(source) for source in source_categories[category])
        source_sections.append(f"<h3>{esc(category_label(category))}</h3><div class=\"source-list\">{cards}</div>")

    article_sections = "".join(
        article_section(
            meeting_dir,
            article,
            article_sources.get(text(article.get("article")), []),
            fincom_by_article.get(text(article.get("article"))),
            motions_by_article.get(text(article.get("article")), []),
            actions_by_article.get(text(article.get("article")), []),
            article_outcome_count > 0,
        )
        for article in articles
    )

    meeting_id = text(manifest.get("meeting_id"), meeting_dir.name)
    official_page = text(manifest.get("official_page_url"))
    preview = meeting_preview(meeting_id, articles, fincom_by_article, motions_by_article, article_outcome_count)
    report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(meeting_id)} Moderator Report</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
  <header>
    <div class="eyebrow">Town Moderator's Toolkit</div>
    <h1>{esc(meeting_id)} Moderator Report</h1>
    <div class="meta">
      <span>{esc(manifest.get('town', ''))}, {esc(manifest.get('state', ''))}</span>
      <span>Retrieved {esc(manifest.get('retrieval_date', 'date unknown'))}</span>
      <span>{link('Official meeting page', official_page)}</span>
    </div>
    <nav class="nav" aria-label="Report sections">
      <a href="#preview">Preview</a>
      <a href="#overview">Overview</a>
      <a href="#prep">Preparation</a>
      <a href="#articles">Articles</a>
      <a href="#sources">Sources</a>
      <a href="#open-items">Open Items</a>
    </nav>
  </header>
  <main>
    <section id="preview">
      <h2>AI-Generated Meeting Preview</h2>
      <div class="news-preview">
        <p class="dek">A local-news style preview generated from parsed warrant articles, Finance Committee recommendations, motions, actions, and source indexes in this meeting folder.</p>
        {preview}
      </div>
    </section>

    <section id="overview">
      <h2>Overview</h2>
      <div class="grid">
        <div class="stat"><strong>{article_count}</strong><span>warrant articles</span></div>
        <div class="stat"><strong>{fincom_count}</strong><span>FinCom recommendations</span></div>
        <div class="stat"><strong>{motion_count}</strong><span>motion/amendment records</span></div>
        <div class="stat"><strong>{article_outcome_count}</strong><span>articles with parsed outcomes</span></div>
        <div class="stat"><strong>{official_count}</strong><span>official source entries</span></div>
        <div class="stat"><strong>{problem_count}</strong><span>items needing review</span></div>
      </div>
    </section>

    <section id="prep">
      <h2>Preparation</h2>
      <div class="panel">
        <p>This report is generated only from the meeting manifest and already archived/parser outputs in this folder. Use it as an index into the article briefs and source materials before the article comes to the floor.</p>
        <p>{badge(parsed_count)} parsed source records {badge(accepted_count)} accepted unofficial records {badge(problem_count, problem_count > 0)} source or review flags</p>
      </div>
      <div class="scroll">
        <table>
          <thead>
            <tr><th>Article</th><th>Title</th><th>Sponsor</th><th>FinCom</th><th>Motions</th><th>Final Action</th></tr>
          </thead>
          <tbody>
            {dashboard_rows(meeting_dir, articles, fincom_by_article, motions_by_article, actions_by_article)}
          </tbody>
        </table>
      </div>
    </section>

    <section id="articles">
      <h2>Articles</h2>
      {article_sections or '<p>No parsed articles are available.</p>'}
    </section>

    <section id="sources">
      <h2>Source Materials</h2>
      <p>Each source card links to the archived local artifact when present, extracted text when present, and the original URL recorded in the manifest.</p>
      {''.join(source_sections) or '<p>No source records are available.</p>'}
    </section>

    <section id="open-items">
      <h2>Open Items</h2>
      <div class="grid">
        <div class="panel"><h3>Manifest</h3>{open_item_list(manifest_open)}</div>
        <div class="panel"><h3>Parser And Review Notes</h3>{open_item_list(combined_open)}</div>
      </div>
    </section>
  </main>
  <footer>
    Generated from local project artifacts. Outcome records: {outcome_count}. Source policy: {esc(manifest.get('source_policy', 'not recorded'))}.
  </footer>
</body>
</html>
"""
    output = meeting_dir / "report.html"
    output.write_text(report, encoding="utf-8")
    return output


def meeting_dirs_from_args(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return sorted(path for path in Path("data/meetings").iterdir() if (path / "manifest.json").exists())
    return [Path(path) for path in args.meeting_dir]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("meeting_dir", nargs="*", help="Meeting folder(s), such as 'data/meetings/SATM 2026'.")
    parser.add_argument("--all", action="store_true", help="Generate reports for every meeting under data/meetings.")
    args = parser.parse_args()
    if not args.all and not args.meeting_dir:
        parser.error("provide one or more meeting folders, or use --all")

    for meeting_dir in meeting_dirs_from_args(args):
        output = generate_report(meeting_dir)
        print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
