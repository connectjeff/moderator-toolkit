# Roadmap

## Priority 1: Source And Meeting Structure

- Done: Create per-meeting folders using names such as `SATM 2026` and `FATM 2025`.
- Done: Maintain a source manifest for each meeting.
- Done: Track which documents have been downloaded, parsed, summarized, and reviewed.
- Done: Separate official sources from background or discovery-only sources in generated briefs.

## Priority 2: Article Briefs

- Done: Extract warrant articles from official warrant documents.
- Started: Attach related motions, amendments, sponsor presentations, and minutes/actions to each article using source-title article numbers.
- Started: Generate moderator-facing draft article summaries using the article brief template.
- Done: Include unresolved-source flags where documents are missing, unparsed, or require reviewer confirmation.

Next:

- Improve article-source matching by parsing document text, not only source titles.
- Add reviewer workflow for confirming draft article briefs.
- Add export-ready moderator packet generation.

## Priority 3: Finance Committee Integration

- Done for SATM 2026: Parse Finance Committee recommendation books when available.
- Started: Capture recommendation status, vote result, unanimity, discussion highlights, and draft for/against extraction aids.
- Surface differences between the warrant language, Finance Committee recommendation, and final motion.

Next:

- Compare parsed article-specific motion documents to the FinCom motion text.
- Replace heuristic for/against bullets with stronger structured summaries grounded in the official discussion text.
- Resolve the current FATM 2025 FinCom source mismatch on the official website before merging FATM recommendation fields.

## Priority 4: Consent Agenda Candidate Analysis

- Done for SATM 2026: Parse the published consent agenda article list from the Finance Committee recommendation book.
- Started: Suggest `good candidate` when an article appears in the official parsed consent agenda list.
- Started: Suggest `not recommended` when a parsed FinCom book exists and the article is excluded from the official consent agenda list.

Next:

- Build consent agenda criteria from Town Meeting Time, Natick rules, and past Natick practice.
- Improve candidate status beyond the official list: `good candidate`, `possible candidate`, `not recommended`, or `needs review`.
- Explain the reason in moderator-facing terms, including known controversy, amendments, financial impact, vote threshold, or procedural complexity.

## Priority 5: Motion And Amendment Integration

- Done: Archive and extract official motion and amendment documents for SATM 2026 and FATM 2025.
- Done: Parse motion document records and classify procedural motions, substitute motions, amendments, consent agenda materials, handouts, and memos.
- Done: Flag blank motion-form templates and PDFs with no extractable text.
- Started: Merge parsed motion details and floor-impact notes into article briefs.

Next:

- OCR or manually review `no_extractable_text` motion PDFs.
- Parse vote thresholds and motion labels more precisely from motion documents.
- Compare motion text to warrant language and FinCom motion text.
- Detect motion dependencies such as "if Article 12 passes/fails."

## Priority 6: Past Meeting Review

- Done for FATM 2025: Summarize final actions and votes by article from official session minutes.
- Started: Compare warrant intent, motion text, Finance Committee recommendation, and final Town Meeting action.
- Track reconsideration, referral, indefinite postponement, amendments, and consent agenda handling.

Next:

- Build a reliable parser for raw voting-system reports so SATM 2026 can get final-action rows even without prose minutes.
- Add a past-meeting dashboard showing action status, vote counts, consent handling, referrals, and articles without parsed final outcomes.
- Distinguish final main-motion result from intermediate procedural outcomes in a compact article status field.

## Priority 7: User Interface

- Provide a meeting dashboard with article status, source coverage, consent agenda suggestions, and floor-readiness notes.
- Add filters for unresolved issues, motions received, Finance Committee positions, and likely procedural complexity.
- Export moderator packets as Markdown, PDF, or Word.

## Priority 8: Multi-Town Configuration

- Add town profiles for charter, bylaws, rules, source URLs, article numbering conventions, vote thresholds, and committee names.
- Keep Natick as the regression test profile while allowing another moderator to configure their own town.
