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

- Review motion/action records flagged as `blank_template` or `no_extractable_text` in each meeting's `working/` JSON outputs.
- Add OCR or manual transcription workflow for official PDFs that cannot be parsed reliably from embedded text.
