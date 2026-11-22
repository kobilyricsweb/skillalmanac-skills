---
name: architecture-decision-records
description: Writes, repairs and audits architecture decision records (ADRs) in an adr/ folder. Use when the user asks to write an ADR, record an architecture decision, supersede or deprecate one, or check or clean up the adr folder or decision log. Makes each record decidable (forcing context, costed options, one decision, consequences) with a status lifecycle and supersede links, and a script scans the folder and prints strict JSON for numbering gaps, missing sections, broken supersede links, accepted ADRs without consequences and duplicate titles. Do not use for design docs or RFCs, code review, meeting minutes, or choosing the technology itself.
license: Apache-2.0
compatibility: The scan script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checks in step 7 and the rule table in the writing guide.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Architecture decision records

An ADR is a short, numbered, immutable-after-acceptance record of one decision. Your job is to record what the team decided and why, from facts the user supplies. You do not make the decision and you do not invent reasons.

## Fixed shape

File `adr/NNNN-slug.md`, NNNN is 3 to 5 digits, never reused. Copy [assets/adr-template.md](assets/adr-template.md). Required, in this order: H1 `# NNNN. Title`; `Status:` line with one of proposed, accepted, rejected, deprecated, superseded; `## Context`; `## Options considered`; `## Decision`; `## Consequences`. Optional lines: `Date:`, `Deciders:`, `Supersedes:`, `Superseded by:`. Front matter (`status`, `supersedes`, `superseded-by`) and MADR headings ("Considered Options", "Decision Outcome") are also read.

## Decidable means

A reader who was not in the meeting can answer yes to all five (details and examples in [references/adr-writing-guide.md](references/adr-writing-guide.md), section 2):

1. Context names the constraint that forced a decision now, with a number where one exists.
2. At least 2 options a sensible person could pick; each states where it wins.
3. Every option, the chosen one too, states one concrete cost.
4. Decision is one sentence: "We will X, because Y", where Y points at a fact in Context.
5. Consequences lists at least one thing that gets worse, who carries it, follow-up work and what would reopen the decision. Under 15 words counts as empty.

## Workflow

```
- [ ] 1 Scan the folder first
- [ ] 2 Decide whether an ADR is warranted
- [ ] 3 Collect the facts; ask for what is missing
- [ ] 4 Number and draft from the template
- [ ] 5 Link and update status
- [ ] 6 Check the five tests
- [ ] 7 Scan again and report
```

1. **Scan first.** `python scripts/adr_scan.py scan adr` (use the folder the repo already uses; `docs/adr`, `docs/decisions` are common). Note existing findings so you can tell them apart from yours. No folder yet: create `adr/` and start at `0001`.
2. **Warranted?** Write one only if reversal would cost more than about two engineer-weeks, or it binds more than one team, or it sets a rule others must follow. Otherwise say a pull request description is enough and stop.
3. **Collect facts.** From the user's message, chat paste or documents take: the forcing constraint, each option actually weighed, the cost of each, who decided, the date. If an option's cost or the deciding reason is missing, ask one question for all gaps. Never fill a gap with a plausible guess. If the user has not decided, the status is `proposed` and Decision starts with "Proposed:".
4. **Number and draft.** Number = highest existing number + 1, even when gaps exist. Slug is 3 to 6 lowercase words naming the choice. Status `accepted` only when the user says it was agreed; otherwise `proposed`. For a decision already made and never written down, follow the retroactive rule in the guide, section 5: record only options that were weighed, and add `Recorded retroactively on <date>`.
5. **Link.** Superseding is four edits in a fixed order: new ADR gets `Supersedes: <old>`; old ADR gets `Status: superseded` and `Superseded by: <new>`; the new Context states what changed since; scan. Change an accepted ADR only in its status and link lines, never its reasoning. Reference other ADRs as `ADR-0007` or by file name so the scanner can follow them.
6. **Check the five tests** above against your draft. Rewrite until each is a yes, or write the gap into the report.
7. **Scan and report.** Run the scan again. `ok` must be `true` and no new finding may come from your files. Fix in the writing guide's rule table order, then re-run. Do not edit `scripts/adr_scan.py` to make a rule pass. Without Python, check by hand: sequential numbers, the five sections present, every Supersedes line mirrored by a Superseded by line, and no accepted ADR with a thin Consequences section.

## Report

```
Created/changed: <files, with number, title, status>
Scan: <ok true/false, errors N, warnings N; remaining findings by rule>
Decidability: <the five tests, each pass or the gap>
Open for a human: <facts the user must supply, options not evaluated, gaps in numbering>
Not checked: <that the options listed are the full set; that cost figures are right>
```

## Script contract

`python scripts/adr_scan.py scan <folder> [--strict]`: run it, do not read it. Reads top-level `*.md` files, skipping README, index and template files. Writes nothing. Prints one JSON object:

```
{"command": "scan", "dir": str, "adr_count": int, "numbers": [int],
 "findings": [{"file": str|null, "line": int|null, "rule": str, "severity": "error"|"warning", "message": str}],
 "counts_by_rule": {rule: int}, "errors": int, "warnings": int, "ok": bool}
```

`ok` is true when there are no errors (with `--strict`, no warnings either). Exit 0 ok, 1 findings, 2 bad usage or no ADR files, with a plain message on stderr. Error rules: duplicate-number, bad-title, title-number-mismatch, missing-status, bad-status, missing-section, empty-section, few-options, accepted-no-consequences, placeholder-text (except on proposed), broken-link, unparsable-link, missing-backlink, superseded-without-successor, successor-status-mismatch, self-reference. Warning rules: bad-filename, numbering-gap, duplicate-title, option-no-downside, thin-consequences, successor-not-accepted. Meaning and fix for each rule: guide section 6. Sources for the format: [references/sources.md](references/sources.md).

## Limits

- The scan checks structure, not truth. It cannot tell whether the options are the real ones or the cost figures are right; `option-no-downside` is a word-list heuristic.
- Consequences under 15 words are treated as empty; one dense sentence over the limit passes even if shallow.
- Gaps in numbering are reported but may be legitimate deletions.
- Only top-level files in one folder are scanned; nested folders and non-Markdown formats are ignored.
- Heading and link parsing covers the shapes listed in Fixed shape. A custom template needs its headings renamed or the scanner reports missing sections.
- The cut-offs (two engineer-weeks, 15 words) are working values, not standards.
- This skill records decisions. It does not weigh technologies or tell the team what to choose.
