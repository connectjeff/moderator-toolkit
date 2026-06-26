# Town Moderator's Toolkit

This project is a working toolkit for preparing for and reviewing Town Meeting. It is designed around official source material only: Massachusetts law, Town Meeting Time, the applicable town charter and bylaws, and official town-published warrant, motion, recommendation, presentation, minutes, and action materials.

The initial test town is Natick, Massachusetts. Meeting artifacts are stored by Town Meeting instance using short folder names such as:

- `SATM 2026` for Spring Annual Town Meeting 2026
- `FATM 2025` for Fall Annual Town Meeting 2025
- `STM 2024` for Special Town Meeting 2024

## Core Outputs

For each warrant article, the toolkit should produce a moderator-facing brief that includes:

- Article identifier, title, sponsor, and official source links.
- Plain-language summary of the article and what Town Meeting is being asked to do.
- Related motions, substitute motions, procedural motions, amendments, and sponsor materials.
- Finance Committee recommendation, vote status, discussion highlights, and summarized arguments for and against when an official recommendation book is available.
- Consent agenda suitability with reasons, cautions, and any known procedural risks.
- Notes for floor management, including likely amendments, vote thresholds, conflicts, special rules, and questions the moderator may need to resolve.

## Source Standard

The toolkit must distinguish official sources from background material. Article summaries and recommendations should be based only on official sources listed in the meeting source manifest.

See [official source policy](docs/official-source-policy.md) and the [article brief template](templates/article-brief.md).

Missing official sources that require manual acquisition are tracked in [TODO](TODO.md).

Town Meeting Time source tracking:

- [TMT4 source status](data/sources/tmt4.md)
- [TMT4 footnote web resources](data/sources/tmt4-footnotes.md)

## Toolkit Commands

The current command-line workflow can:

- Build a source manifest from an official Natick Town Meeting page.
- Archive selected official source documents with checksums.
- Extract text from archived warrant and Finance Committee PDFs.
- Parse warrant articles into structured JSON.
- Generate draft article briefs.

See [current workflow](docs/workflow.md).

## Current Test Meetings

- [SATM 2026](data/meetings/SATM%202026/README.md)
- [FATM 2025](data/meetings/FATM%202025/README.md)

## Development Roadmap

See [roadmap](docs/roadmap.md) for the prioritized feature list.
