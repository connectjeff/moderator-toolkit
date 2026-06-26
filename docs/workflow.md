# Current Workflow

This workflow builds source-backed draft article briefs for a Natick Town Meeting folder.

## 1. Build Or Refresh The Manifest

Fetch the official meeting page and create `manifest.json`:

```sh
python3 tools/ingest_natick_meeting.py \
  --meeting-id "SATM 2026" \
  --title "2026 Spring Annual Town Meeting" \
  --url "https://www.natickma.gov/2347/2026-Spring-Annual-Town-Meeting" \
  --meeting-dir "data/meetings/SATM 2026"
```

To regenerate from already archived HTML:

```sh
python3 tools/ingest_natick_meeting.py \
  --meeting-id "SATM 2026" \
  --title "2026 Spring Annual Town Meeting" \
  --url "https://www.natickma.gov/2347/2026-Spring-Annual-Town-Meeting" \
  --meeting-dir "data/meetings/SATM 2026" \
  --html-file "data/meetings/SATM 2026/sources/official-meeting-page.html"
```

## TMT4 Footnote Sources

Refresh the official TMT4 footnote web-resource registry:

```sh
python3 tools/ingest_tmt4_footnotes.py
```

Outputs:

- `data/sources/tmt4-footnotes.json`
- `data/sources/tmt4-footnotes.md`

If an official source is not publicly available, add it to `TODO.md` instead of using an unofficial replacement.

## 2. Archive High-Value Official Sources

Download and checksum the official warrant and Finance Committee recommendation book:

```sh
python3 tools/archive_manifest_sources.py \
  --manifest "data/meetings/SATM 2026/manifest.json" \
  --categories warrant finance_committee \
  --official-only
```

## 3. Extract PDF Text

Use the bundled Codex Python runtime because it includes `pypdf`:

```sh
/Users/jeffalderson/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/extract_archived_pdf_text.py \
  --manifest "data/meetings/SATM 2026/manifest.json" \
  --categories warrant finance_committee
```

## 4. Parse Warrant Articles

```sh
python3 tools/parse_warrant_articles.py \
  --meeting-id "SATM 2026" \
  --input "data/meetings/SATM 2026/working/extracted-text/2026-satm-warrant-approved-3-2-2026-docx-1-1.txt" \
  --output "data/meetings/SATM 2026/working/warrant-articles.json"
```

## 5. Build Article Source Index

```sh
python3 tools/build_article_source_index.py \
  --manifest "data/meetings/SATM 2026/manifest.json" \
  --output "data/meetings/SATM 2026/working/article-source-index.json"
```

## 6. Parse Finance Committee Recommendations

```sh
python3 tools/parse_fincom_recommendations.py \
  --meeting-id "SATM 2026" \
  --input "data/meetings/SATM 2026/working/extracted-text/fincom-recommendation-book-satm26.txt" \
  --output "data/meetings/SATM 2026/working/fincom-recommendations.json"
```

The parser extracts:

- Recommendation.
- Vote quantum.
- Unanimity status.
- Date voted.
- Motion vote threshold.
- Discussion text.

If the FinCom book header does not match the meeting ID, generated briefs will show a source warning and will not merge the mismatched recommendation records.

## 7. Parse Motion And Amendment Documents

Archive official motion and amendment PDFs:

```sh
python3 tools/archive_manifest_sources.py \
  --manifest "data/meetings/SATM 2026/manifest.json" \
  --categories motion_or_amendment \
  --official-only
```

Extract PDF text:

```sh
/Users/jeffalderson/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/extract_archived_pdf_text.py \
  --manifest "data/meetings/SATM 2026/manifest.json" \
  --categories motion_or_amendment
```

Parse motion records:

```sh
python3 tools/parse_motion_documents.py \
  --manifest "data/meetings/SATM 2026/manifest.json" \
  --output "data/meetings/SATM 2026/working/motions.json"
```

The parser classifies motion records as `motion`, `procedural_motion`, `substitute_motion`, `amendment`, `memo`, `handout`, or `document`. Archived consent agenda motions are kept as meeting source material, but the toolkit does not assemble or recommend consent agendas.

## 8. Parse Final Actions From Official Minutes

Archive official minutes/action PDFs:

```sh
python3 tools/archive_manifest_sources.py \
  --manifest "data/meetings/FATM 2025/manifest.json" \
  --categories minutes_or_actions \
  --official-only
```

Extract PDF text:

```sh
/Users/jeffalderson/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  tools/extract_archived_pdf_text.py \
  --manifest "data/meetings/FATM 2025/manifest.json" \
  --categories minutes_or_actions
```

Parse official final actions:

```sh
python3 tools/parse_action_documents.py \
  --manifest "data/meetings/FATM 2025/manifest.json" \
  --output "data/meetings/FATM 2025/working/actions.json"
```

The parser currently extracts article outcomes from official session-minutes documents. Raw voting-system reports are archived and extracted, but are not treated as final article outcomes unless a later parser can reliably map the vote columns to article actions.

## 9. Generate Draft Article Briefs

```sh
python3 tools/generate_article_briefs.py \
  --warrant-articles "data/meetings/SATM 2026/working/warrant-articles.json" \
  --article-source-index "data/meetings/SATM 2026/working/article-source-index.json" \
  --fincom-recommendations "data/meetings/SATM 2026/working/fincom-recommendations.json" \
  --motions "data/meetings/SATM 2026/working/motions.json" \
  --actions "data/meetings/SATM 2026/working/actions.json" \
  --output-dir "data/meetings/SATM 2026/articles"
```

## Current Review Notes

- SATM 2026 parsed 18 warrant articles.
- SATM 2026 parsed 18 Finance Committee article recommendation sections.
- SATM 2026 parsed 9 official motion/amendment documents: 4 substantive parsed records and 5 blank motion-form templates requiring review.
- SATM 2026 archived and extracted 2 official voting-system reports, but no official session-minutes prose was available in the manifest for final-action parsing.
- FATM 2025 parsed 33 warrant articles.
- FATM 2025 parsed 33 Finance Committee article recommendation sections from the Google Drive alternate source. The original Natick page link downloaded a Spring Annual Town Meeting 2026 recommendation book and remains recorded in the manifest as `source_mismatch`.
- FATM 2025 parsed 21 official motion/amendment documents: 14 substantive parsed records, 5 records needing OCR/manual text review, and 2 blank motion-form templates.
- FATM 2025 parsed 60 official final-action outcome records from session minutes, covering all 33 articles.
- SATM 2025 parsed 25 warrant articles.
- SATM 2025 parsed 25 Finance Committee article recommendation sections.
- SATM 2025 parsed 10 official motion/amendment documents: 6 substantive parsed records and 4 blank motion-form templates requiring review.
- SATM 2025 parsed 59 official final-action outcome records, covering 8 articles.
- SATM 2025 also parsed 25 accepted unofficial vote-result records from the Finance Committee Google workspace spreadsheet linked on the official meeting page. The source remains marked `official: false` and `accepted_unofficial: true`.
- Draft article briefs are conservative. They now include parsed FinCom recommendation fields where the source passes the meeting-header check, parsed motion/amendment details where text is available, and parsed final actions where official session minutes are available.
- FATM draft article briefs now include parsed final-action rows from official session minutes.
- Draft for/against bullets are heuristic extraction aids and require reviewer confirmation.
