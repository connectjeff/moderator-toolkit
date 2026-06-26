# TODO

## Official Sources To Obtain Manually

- Obtain a lawful official copy of `Town Meeting Time, 4th Edition` in PDF or another usable format and add it under `data/sources/tmt4/`.
  - Do not use unofficial scans or unverified copies.
  - Once added, record title, edition, publisher, copyright/provenance note, local path, and retrieval/acquisition date in `data/sources/tmt4.md`.
- Obtain any town-specific charter, bylaw, zoning bylaw, rule, warrant, motion, recommendation, minutes, or action documents that are not available from an official public URL.
  - Store town-wide sources under `data/sources/`.
  - Store meeting-specific sources under the relevant `data/meetings/<MEETING>/sources/` folder.
  - Add provenance notes to the meeting `manifest.json` before using the source in article briefs.

## Source Review Items

- Review the FATM 2025 Finance Committee recommendation source. The official Natick link currently resolves to a Spring Annual Town Meeting 2026 recommendation book, so FATM recommendation fields are intentionally not merged into briefs.
- Confirm whether an official SATM 2025 consent agenda source exists. No consent agenda document was found on the official meeting page or parsed from the official Finance Committee recommendation book.
- Determine whether the SATM 2025 `Voting Results (Unofficial)` spreadsheet has an official equivalent before using it for final-action summaries.
- Review motion/action records flagged as `blank_template` or `no_extractable_text` in each meeting's `working/` JSON outputs.
- Add OCR or manual transcription workflow for official PDFs that cannot be parsed reliably from embedded text.
