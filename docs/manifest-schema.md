# Meeting Manifest Schema

Each Town Meeting folder should contain a `manifest.json` file generated from official source pages and reviewed as source material changes.

## Top-Level Fields

- `meeting_id`: Short meeting identifier, such as `SATM 2026`.
- `town`: Town name.
- `state`: State abbreviation.
- `official_page_url`: Official meeting page URL.
- `retrieved_at`: ISO-8601 timestamp for the source-page retrieval.
- `retrieval_date`: Local date of retrieval.
- `source_policy`: Path to the project source policy used for interpretation.
- `sources`: Array of source entries.
- `open_items`: Known missing, uncertain, or review-needed items.

## Source Entry Fields

- `id`: Stable slug for the source entry.
- `title`: Link text or document title from the official page.
- `url`: Absolute URL.
- `category`: Normalized category, such as `warrant`, `finance_committee`, `motion_or_amendment`, `presentation`, `minutes_or_actions`, `resource`, or `meeting_page`.
- `source_type`: `web_page`, `document`, `spreadsheet`, `video`, or `unknown`.
- `official`: Boolean. For Natick meeting manifests, links from the official Town Meeting page are treated as official unless marked otherwise.
- `accepted_unofficial`: Optional boolean. Use only for non-official sources that the project has explicitly accepted under `docs/official-source-policy.md`, such as Finance Committee Google workspace vote-result files linked from an official meeting page.
- `acceptance_basis`: Optional string explaining why an accepted unofficial source may be used and how it must be labeled.
- `listed_on_official_page`: Boolean.
- `retrieved_at`: Timestamp when the manifest was generated.
- `local_path`: Local artifact path if downloaded or archived.
- `status`: `identified`, `archived`, `parsed`, `summarized`, `reviewed`, or `needs_review`.
- `notes`: Free-text provenance or review notes.

## Article Brief Relationship

Article briefs should cite only manifest source entries unless a reviewer explicitly adds another official source to the manifest. When generated article briefs refer to a document, they should use the source `id` and URL from `manifest.json`.
