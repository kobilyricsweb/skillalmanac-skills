# Listing page content: architecture-decision-records

**One line:** Writes and audits ADRs that a stranger can act on, and scans the adr folder for broken numbering, links and missing sections.

## What it does

The skill gives an agent a fixed ADR shape (title, status, context, options considered, decision, consequences), five tests that make a record decidable, and exact edit sequences for the status lifecycle (proposed, accepted, rejected, deprecated, superseded). A scan script reads the folder and prints strict JSON: numbering gaps and duplicates, missing or empty sections, supersede links that point at nothing or are not mirrored, accepted ADRs with no real consequences, one-option "decisions", duplicate titles and leftover TBDs. It also tells the agent what not to do: invent options, invent reasons, or rewrite an accepted record instead of superseding it.

## Capabilities

- `scripts/adr_scan.py scan <folder> [--strict]`: JSON with 22 rule names, errors and warnings separated, line numbers where known
- `assets/adr-template.md`: the record template
- A writing guide: when an ADR is warranted, the five decidability tests, retroactive records, the rule-by-rule fix table
- A fixed report: what changed, scan result, which tests pass, what a human must supply, what was not checked

## When to use

You say write an ADR, record this decision, supersede ADR 7, deprecate that record, or check/clean up our adr folder.

## When not to use

Design docs and RFCs, code review, meeting minutes, or picking the technology (the skill records a decision; it does not weigh options for the team).

## How it differs from nearby skills

`decision-evidence-ledger` (batch 3) and `decision-council` (batch 5) are about collecting evidence for, or debating, a decision in general. This skill starts after the team has decided or is about to, and is specific to the ADR file format, its lifecycle and its folder-level integrity checks.

The installed `engineering:architecture` plugin skill helps think through and write a decision. This skill adds what that one does not have: a folder-level script that checks numbering gaps, broken supersede links, status mismatches and missing sections across all ADR files, plus the supersede edit order.

## Requirements

Python 3.9 or newer for the scan (standard library only). No network. Without Python the agent follows the manual checks in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so no saved edit is shown. What exists is the scanner on the saved fixtures (run from the skill folder):

1. `python scripts/adr_scan.py scan evals/fixtures/good/adr`: 4 ADRs, `findings: []`, `ok: true`, exit 0. The set includes a superseded record, its replacement with the mirrored link, and a proposed record with a short but real consequences note.
2. `python scripts/adr_scan.py scan evals/fixtures/bad/adr`: 8 ADRs, 10 errors, 6 warnings, `ok: false`, exit 1. Excerpt of the findings:

```
numbering-gap                 missing numbers between 1 and 10: 2, 9
0003-adopt-graphql-gateway    accepted-no-consequences, placeholder-text
0005-queue-for-emails         broken-link (superseded by 0009, no such file)
0006-choose-cache             bad-status 'approved', missing-section (options)
0007-single-region            missing-backlink (0001), few-options
0008-pick-ci                  title-number-mismatch (title 9, file 8), broken-link (ADR-0042)
0010-retire-soap-api          superseded-without-successor
```

## Limits

- The scan checks structure, not truth: it cannot tell whether the options are the real ones or the figures are right; the downside check is a word-list heuristic.
- Consequences under 15 words count as empty.
- Numbering gaps may be legitimate deletions.
- One folder, top level only, Markdown only.
- The cut-offs are working values, not standards.

## Evidence

See `VERIFICATION.md`. In short: static lint passed, and the 9 fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A folder with a half-finished history; run the scan: 10 errors on screen.
2. The user pastes a chat message about moving off RabbitMQ; the agent asks one question about a missing cost.
3. The agent writes ADR 0003, flips 0001 to superseded and links both ways.
4. Scan again: `ok: true`; the report lists what a human still has to confirm.

## FAQ seeds

- Does it need network access? No.
- Will it make up reasons for a decision? The skill forbids it; missing facts are asked for or left as gaps in the report. Not yet measured against a baseline.
- Does it work with MADR files? Yes for the usual headings and front matter (status, supersedes, superseded-by); custom templates need their headings renamed.
- Can it edit an accepted ADR? Only the status and link lines; changed reasoning means a new, superseding ADR.
- Where do the records live? Wherever the repo already keeps them; the agent scans that folder first.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
