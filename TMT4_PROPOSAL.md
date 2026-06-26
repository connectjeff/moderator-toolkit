# Proposal: Licensed Use of Town Meeting Time, 4th Edition in the Town Moderator's Toolkit

## Executive Summary

The Town Moderator's Toolkit is a source-first project for helping Massachusetts Town Moderators prepare for, conduct, and review Town Meeting. The current prototype uses official town meeting materials, Massachusetts law, town bylaws, warrants, motions, minutes, action reports, and Finance Committee recommendation books. The project intentionally tracks provenance for every source and distinguishes official materials from background or unverified materials.

This proposal asks the Massachusetts Moderators Association and the authors of `Town Meeting Time, 4th Edition` (`TMT4`) to consider allowing licensed, controlled use of the raw text or PDF text of TMT4 inside this toolkit.

The purpose is not to create an AI replacement for TMT4. The purpose is to make TMT4 more usable by moderators who already have lawful access to it, while preserving exact citation, page/section traceability, copyright protection, and user-facing warnings when the toolkit cannot support an answer from the official text.

## Project Background

The toolkit is being developed as a moderator-facing workspace with these goals:

- Organize official Town Meeting source materials by meeting instance, such as `SATM 2026` or `FATM 2025`.
- Generate article briefs from official warrant, motion, recommendation, and action materials.
- Help moderators identify article-specific materials, procedural issues, vote thresholds, amendments, and final action history.
- Provide a report page for each meeting with an overview, preparation table, source traceability, and article-specific notes.
- Keep Natick, Massachusetts as the initial regression-test town while designing the project so another moderator can configure their own town.

The project already tracks TMT4 as an official source that must be obtained lawfully before use. It also records the public TMT4 footnote web resources published by the Massachusetts Moderators Association at:

https://massmoderators.org/tmt4-footnote/

## Why TMT4 Matters

Town Meeting procedure is not an area where AI should improvise. A moderator needs the actual rule, the relevant authority, and the limits of that authority. TMT4 is valuable because it presents procedural guidance in context, with references and footnotes. If TMT4 is available to the toolkit under appropriate conditions, the toolkit can help moderators find and apply that material faster while preserving the book as the authoritative source.

The toolkit should treat TMT4 as a controlled reference work, not as training data to be absorbed into a general model.

## Author Concerns This Proposal Addresses

The authors have raised appropriate concerns:

- AI tools can hallucinate rules, citations, or procedural authority.
- TMT4 citations must be exact.
- Usage must point back to the specific text, section, page, footnote, and cited authority.
- Users must be able to click through to original content where the cited authority is available online.
- Copyright must be respected.
- Access to raw text must be limited to those with a valid license or lawful copy.

This proposal accepts those concerns as design requirements.

## Core Safeguards

### 1. Retrieval-Only Answers for TMT4

The toolkit should not answer TMT4 questions from model memory.

For any question about Town Meeting rules, procedure, moderator authority, motions, debate, reconsideration, amendments, vote thresholds, quorum, points of order, scope, decorum, or related matters, the toolkit should:

1. Retrieve relevant passages from the licensed TMT4 source index.
2. Retrieve any cited TMT4 footnotes or external official authorities where available.
3. Produce an answer only if the retrieved material supports it.
4. Cite the exact TMT4 section, page, heading, and footnote references used.
5. Provide links to online source materials when those links are part of the TMT4 footnotes or official public sources.
6. Refuse or mark unresolved when no adequate source passage is retrieved.

### 2. No Citation, No Answer

The answer policy should be:

> If the toolkit cannot cite TMT4 or another official source for a procedural claim, it must not present that claim as an answer.

Instead, it should say something like:

> I do not have a cited TMT4 passage or official source that supports an answer to this question. Please consult TMT4 directly or add the relevant official source to the project.

### 3. Exact Citation Records

Every indexed TMT4 passage should carry structured metadata:

- Title: `Town Meeting Time, 4th Edition`
- Edition
- Publisher / rights holder
- Copyright notice or provenance note
- Page number
- Chapter
- Section number
- Heading
- Paragraph or passage identifier
- Footnote numbers present in the passage
- Links to public footnote sources when available
- Local source checksum
- Extraction date
- Access-control status

Generated answers should show these references in a source block such as:

```text
Sources:
- TMT4, 4th ed., Section 6.2, p. __, "____", footnotes __ and __.
- TMT4 footnote __: https://...
- M.G.L. c. __, Section __: https://malegislature.gov/...
```

### 4. Quoted Text Limits and Exactness

The toolkit should distinguish:

- short exact quotations from TMT4;
- paraphrases of TMT4;
- direct citations to TMT4;
- links to public footnote authorities;
- moderator notes or workflow suggestions.

For copyright protection, the default interface should avoid long TMT4 quotations. It should provide short excerpts only when needed to verify the cited point, and otherwise direct licensed users to the page/section in their lawful copy.

### 5. Page Image / PDF Location Anchors

If the licensed source is a PDF, each indexed passage should retain a pointer back to the page location in the original PDF. A moderator should be able to click from an answer to the relevant page in their authorized local copy or in an authenticated viewer.

### 6. Source Conflict Handling

When TMT4, Massachusetts law, a town charter/bylaw, or local adopted Town Meeting rules appear to differ, the toolkit should not resolve the conflict on its own. It should instead flag the conflict:

```text
Potential source conflict:
- TMT4 says/references: ...
- Natick bylaw/rule says: ...
- Massachusetts law says: ...

Moderator review required before floor use.
```

### 7. Audit Logs

For any generated procedural answer, the toolkit should record:

- user question;
- retrieved TMT4 passages;
- retrieved external authorities;
- generated answer;
- citations shown to user;
- unanswered or unresolved status if applicable;
- timestamp;
- user/license context, if authentication is used.

This creates an audit trail for correcting errors and demonstrating that the answer came from licensed source text.

## Proposed Answering Process

The TMT4 workflow should be intentionally conservative:

1. User asks a procedural question.
2. Query classifier determines whether the question requires TMT4 or legal/procedural authority.
3. Retriever searches only approved indexes: TMT4, Massachusetts law, town charter/bylaws/rules, and official meeting materials.
4. Candidate passages are ranked.
5. The answer generator receives only the retrieved passages and metadata.
6. The answer generator must cite each procedural statement.
7. A citation verifier checks that every citation exists in the retrieved source set.
8. A quote verifier checks that any quoted language matches the extracted source text.
9. If verification fails, the answer is blocked and returned for review or shown as unresolved.
10. The final answer displays citations and links.

## Prototype Examples

These examples are illustrative. They use placeholder TMT4 references until the official licensed text is available.

### Example 1: Procedural Question

Question:

```text
Can the moderator rule an amendment out of scope?
```

Prototype answer:

```text
TMT4 appears to treat amendment scope as a moderator-facing procedural question, but the toolkit cannot give a final answer unless the relevant TMT4 passage is retrieved and cited.

Retrieved authority needed:
- TMT4 section on amendments and scope, exact page and section.
- Any cited Massachusetts authority or TMT4 footnote source.
- Any local Town Meeting rule that modifies amendment practice.

Status: unresolved until cited TMT4 text is available.
```

If licensed text is available, the answer would become:

```text
Short answer:
Yes, if the cited TMT4 section and any local rule support that ruling. The moderator should identify the warrant article's scope, compare the amendment to that scope, and state the ruling with the applicable authority.

Sources:
- TMT4, 4th ed., Section __, p. __, "____".
- TMT4 footnote __: [public link if available].
- Local rule: [town rule citation if available].
```

### Example 2: Article Brief Enrichment

For a warrant article with an amendment, the toolkit could add a source-backed procedural note:

```text
Floor attention:
An amendment has been submitted for Article 18. Before the article comes to the floor, review TMT4 Section __ on amendments, including the cited discussion of scope and order of consideration. Also check Natick's adopted Town Meeting rules for any local requirements.

Sources:
- TMT4, 4th ed., Section __, p. __.
- Natick Town Meeting rules, Section __.
- Article 18 Amendment Foss, official meeting source.
```

### Example 3: Moderator Preparation Checklist

The toolkit could generate a checklist:

```text
Before Article 12:
- Confirm whether the main motion requires a majority, two-thirds, or other vote threshold.
- Review TMT4 Section __ on vote thresholds.
- Review the local charter/bylaw provision cited by the article.
- Confirm whether the motion text differs from the warrant language.
- Prepare a ruling path if a point of order is raised.
```

Every checklist item would include a citation or be labeled as a workflow reminder rather than procedural authority.

### Example 4: Citation-First Search

Search:

```text
"reconsideration"
```

Prototype result:

```text
TMT4 matches:
- Section __, p. __: "Reconsideration..." [short excerpt]
- Section __, p. __: "..." [short excerpt]

Related public footnote sources:
- Footnote __: https://...

Open in licensed copy:
- tmt4://section/__/page/__
```

### Example 5: Refusal When Unsupported

Question:

```text
Can I end debate whenever I think the discussion has gone on long enough?
```

Prototype response:

```text
I cannot answer that as a procedural rule without a retrieved citation from TMT4, Massachusetts law, or the local Town Meeting rules. Please review the cited TMT4 sections on debate, motions to close debate, and moderator authority.

Status: citation required.
```

## Possible Features If Official TMT4 Text Is Available

### High Priority

- Citation-first procedural Q&A for moderators.
- TMT4 section/page lookup with short excerpts and page links.
- Footnote-aware answers that click through to public source material where available.
- Article brief procedural notes tied to specific motions, amendments, vote thresholds, and floor risks.
- Source conflict detection between TMT4, Massachusetts law, town bylaws, and adopted Town Meeting rules.
- Moderator preparation checklist for each article.
- Exact citation verifier for generated answers.
- Quote verifier to ensure any quoted TMT4 language exactly matches the licensed text.

### Medium Priority

- Motion classification help: main motion, amendment, substitute motion, procedural motion, referral, reconsideration, indefinite postponement.
- Vote threshold assistant that cites TMT4 plus Massachusetts law or local rules.
- Decorum and debate guidance with citation-backed prompts.
- Point-of-order preparation guide.
- Town-specific procedural profile combining TMT4 with local charter/bylaw/rule material.
- Search index for TMT4 footnotes and cited public authorities.
- Meeting-night quick reference view for common moderator questions.

### Longer-Term Possibilities

- Authenticated TMT4 reader for licensed users.
- Side-by-side comparison of TMT4 guidance, town rules, and relevant statutes.
- Training mode for new moderators using citation-backed scenarios.
- Review workflow where experienced moderators approve or annotate generated procedural notes.
- Exportable moderator bench book for a specific meeting, with TMT4 references but without reproducing copyrighted text beyond permitted excerpts.

## Copyright and Access-Control Options

The project can support several models, depending on what the Massachusetts Moderators Association and authors prefer.

### Option 1: User-Supplied Local Copy

Each licensed user places their own lawful PDF or text copy in a local, ignored folder such as:

```text
data/sources/tmt4/private/
```

Safeguards:

- The raw TMT4 file is not committed to Git.
- `.gitignore` excludes the private source directory.
- The toolkit stores only local checksums and metadata.
- Generated outputs contain citations and short excerpts only.
- The user's local machine performs retrieval.

Best for:

- Individual moderators using the toolkit privately.
- Lowest centralized copyright risk.

Tradeoff:

- Harder to support web/cloud use.
- Each user must manage their own copy.

### Option 2: Encrypted Local Source Bundle

The MMA distributes an encrypted TMT4 source bundle to licensed users.

Safeguards:

- The toolkit can read the bundle only after the user enters a license key or unlock token.
- Raw text remains encrypted at rest.
- Only passage snippets needed for the current answer are decrypted in memory.
- No raw text is stored in generated public artifacts.

Best for:

- Desktop app or local command-line use.

Tradeoff:

- Requires license-key and encryption tooling.

### Option 3: Authenticated MMA Retrieval API

The MMA hosts a secure retrieval service.

Safeguards:

- The toolkit sends a query to the MMA service.
- The service authenticates the user as a licensed TMT4 holder or MMA member.
- The service returns only approved passage snippets, page/section metadata, and citation data.
- The toolkit never receives or stores the full raw text.

Best for:

- Strongest centralized copyright control.
- Web or multi-device use.

Tradeoff:

- Requires MMA-hosted infrastructure.

### Option 4: Citation Index Only in the Toolkit

The toolkit stores a non-expressive citation index:

- section headings;
- page numbers;
- keywords;
- footnote numbers;
- public footnote URLs;
- no substantial TMT4 prose.

Safeguards:

- Users search the index.
- The toolkit points users to the section/page in their purchased copy.
- It does not quote or paraphrase TMT4 beyond minimal metadata.

Best for:

- Conservative copyright posture.
- Public open-source repository compatibility.

Tradeoff:

- Less useful for procedural Q&A.
- More manual lookup for moderators.

### Option 5: Licensed Cloud Workspace

The toolkit runs in a private cloud workspace available only to authenticated licensed users.

Safeguards:

- Access controlled by MMA membership and proof of TMT4 purchase.
- Raw text stored in a restricted private data store.
- Outputs watermarked or logged.
- Rate limits and excerpt limits enforced.
- No raw text in public repository.

Best for:

- Shared hosted tool.

Tradeoff:

- Requires governance, hosting, and operational policies.

### Option 6: Hybrid Model

Use a public citation index plus one of the controlled raw-text models above.

Example:

- Public repository stores TMT4 metadata, footnote links, schemas, and tests.
- Licensed users unlock raw text locally or through MMA authentication.
- Public reports show citations and page references.
- Private reports for licensed users may include short verified excerpts.

Best for:

- Open development with protected copyrighted content.
- Practical balance between usability and rights protection.

## Recommended Initial Approach

For an initial pilot, the safest approach is:

1. Do not commit raw TMT4 text to the public repository.
2. Add a private local source folder ignored by Git.
3. Allow a small number of licensed testers to add their own lawful copy locally.
4. Build the TMT4 index from that local copy.
5. Generate citation-backed answers and reports locally.
6. Log every answer with retrieved passages and citations.
7. Review sample outputs with the authors before wider release.

This approach lets the authors evaluate the quality and safeguards without distributing the raw text through the project.

## Proposed Technical Controls

- `tmt4_manifest.json`: records source metadata, edition, checksum, extraction date, and license mode.
- `tmt4_index.jsonl`: passage index with section/page metadata and limited search text, stored privately unless approved.
- `tmt4_citations.json`: structured citation map from passages to section/page/footnotes.
- `tmt4_footnotes.json`: public footnote resources already available from MMA.
- `answer_trace.json`: per-answer retrieval and citation audit log.
- Citation verifier: blocks unsupported procedural claims.
- Quote verifier: compares quoted text to extracted source text.
- Excerpt limiter: prevents long TMT4 excerpts in generated outputs.
- Public/private output modes:
  - public mode: citations and page references only;
  - licensed mode: citations plus short excerpts;
  - reviewer mode: retrieved passages visible for validation.

## Proposed Editorial Controls

- Every TMT4-enabled feature should be marked as draft until reviewed.
- Generated procedural notes should include a "review before floor use" status.
- The toolkit should not provide legal advice.
- The toolkit should identify when local rules or statutes may supersede or modify general TMT4 guidance.
- The authors or MMA reviewers should be able to provide corrections or preferred citation formats.
- The citation format should be approved before public release.

## What the Toolkit Will Not Do

The toolkit should not:

- train a public AI model on TMT4 text;
- expose the full raw TMT4 text in a public repository;
- answer procedural questions without citations;
- fabricate section numbers, page numbers, footnotes, or authorities;
- treat generated output as a substitute for moderator judgment;
- override Massachusetts law, local charter/bylaw provisions, or adopted Town Meeting rules;
- reproduce substantial copyrighted text unless expressly licensed.

## Requested Permission for Pilot

The project requests permission to conduct a limited pilot using official TMT4 text under one of the copyright/access models above.

The pilot would produce:

- a private indexed copy of TMT4 for licensed testers only;
- sample citation-backed procedural answers;
- sample article brief procedural notes;
- sample source trace logs;
- a list of cases where the toolkit refused to answer because the source support was insufficient;
- review materials for the authors and MMA before broader use.

## Success Criteria

The pilot should be considered successful only if:

- every procedural answer includes exact TMT4 citations or refuses to answer;
- quoted language exactly matches the source text;
- links to public footnote authorities work where available;
- no raw TMT4 text is exposed to unlicensed users;
- reviewers can reproduce how each answer was generated;
- the authors are satisfied that the citation format and source limitations preserve the integrity of TMT4.

## Open Questions for the Authors and MMA

- What citation format should the toolkit use for TMT4?
- Are short excerpts permissible for licensed users? If so, what length limits should apply?
- Should page images or PDF page links be exposed inside the tool?
- Would MMA prefer local-only use, an authenticated retrieval API, or another model?
- Can the public TMT4 footnote page be treated as an official citation target for linked footnotes?
- Should generated procedural answers be labeled "draft moderator research" or another preferred phrase?
- Would the authors be willing to review a small set of prototype outputs before any release?

## Conclusion

TMT4 can make the Town Moderator's Toolkit substantially more useful, but only if it remains the authority rather than becoming hidden background material. The proposed approach is citation-first, retrieval-only, and conservative: the toolkit should answer only when it can show the exact source path back to TMT4 and related official authorities. Where it cannot do that, it should refuse, flag the issue, or ask for human review.

The goal is to help moderators use TMT4 more accurately, not to dilute or replace it.
