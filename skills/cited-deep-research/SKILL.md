---
name: cited-deep-research
description: Runs a research task as a fixed, auditable procedure (decompose the question, log every source with URL, access date and verbatim quote, build a claim table of claim, source id, quote and confidence, handle contradictions) and delivers a report where every paragraph cites, checked by a script that outputs strict JSON. Use when the user wants a sourced or cited research report, deep research with traceable claims, a source log, or an existing report checked for unsupported claims. Do not use for quick factual answers, formatting citations in APA or MLA, market sizing, or plagiarism checks.
license: Apache-2.0
compatibility: The checker script needs Python 3.9 or newer, standard library only. No network access is used by the script; reading sources needs whatever web or file access the agent already has. Without Python, follow the manual checks in step 8.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
  license: Apache-2.0
  author_model: claude-sonnet-5-5
---

# Cited deep research

A research report is only as good as the reader's ability to check it. This procedure makes every statement point to a quote in a page you actually opened, and gives the reader the confidence you hold and why. Domain-neutral: it governs how evidence is recorded, not what the topic is.

## Rules that never bend

1. A source enters the log only after you opened it and read the passage. A search snippet is a lead, not a source.
2. The quote is copied from the opened text, not recalled. Keep it to the sentence you rely on.
3. No claim without a source id and a quote. If nothing supports it, it is not a finding: move it to Gaps.
4. Confidence belongs to the claim, not to your mood. Use the scale in step 4.
5. Never average, merge or smooth conflicting sources. Record both.
6. Do not edit `scripts/validate_research.py` to make a check pass.

## Workflow

```
- [ ] 1 Pin and decompose the question
- [ ] 2 Plan sources per sub-question
- [ ] 3 Read and log sources (sources.md)
- [ ] 4 Write the claim table
- [ ] 5 Resolve contradictions
- [ ] 6 Write the report
- [ ] 7 Run the checker, fix, re-run
- [ ] 8 Deliver with the fixed summary
```

1. **Pin and decompose.** Write the question in one sentence, then scope: time window, region, definitions of any term that could be read two ways. Split into 3 to 7 sub-questions. Each gets a done-condition ("a figure with a date and its method", "the decision and who made it"). Show this to the user if the scope is ambiguous and the answer would change; otherwise proceed and state the scope in the report.
2. **Plan sources.** For each sub-question list the kind of source that would settle it, best first: the originating document or dataset, then an independent analysis, then reporting about it, then commentary. Note independence: two articles repeating one press release are one source. Details and tier examples: [references/sources-and-contradictions.md](references/sources-and-contradictions.md).
3. **Read and log.** Open each source. Add one row to `sources.md` immediately: id (`S1`, `S2`, ...), title, url, accessed date (`YYYY-MM-DD`, the day you opened it), quote. Log pages that were dead, paywalled or irrelevant in your working notes, not in the table. If a page cannot be opened, say so in Gaps; do not cite it from memory.
4. **Claim table.** One row per atomic claim: `claim_id` (`C1`, ...), the claim in one sentence, `source_ids`, a `quote` that is a verbatim fragment of what the cited source's logged quote says, and `confidence` from 0.0 to 1.0:

   | Range | Meaning |
   |---|---|
   | 0.85 to 1.0 | Primary source states it directly, and an independent source agrees |
   | 0.65 to 0.84 | One primary source states it, or two independent secondary sources agree |
   | 0.45 to 0.64 | One secondary source, or a source with a known stake, or an inference of one step |
   | 0.25 to 0.44 | Hearsay, anonymous, undated or unverifiable; show it only as a rumour |
   | below 0.25 | Do not state as a finding; list in Gaps |

   A single source above 0.8 is flagged by the checker: justify it or lower it.
5. **Contradictions.** When two claims cannot both hold, add a row to the Contradictions table: topic, the claim ids, resolution. Test in this order: different definition or population, different date, different measurement method, higher-tier source against lower, one source copying the other. If one explanation fits, say which and why. If none does, resolution is `unresolved` and the report shows both numbers. Lower confidence on claims that stay in conflict. The script cannot find a conflict you did not list, so before validating, compare by hand every pair of claims on the same topic that carry different numbers or dates, and add a row for each that disagrees.
6. **Write the report** to the contract below. Use claim ids in text, `[C1]` or `[C1, C2]`; the table maps them to sources.
7. **Check.** Run:

```bash
python scripts/validate_research.py report.md sources.md
```

   It prints one JSON object: `ok`, `counts`, `errors`, `warnings`; each item has `code`, `where`, `message`. Exit 0 means no errors, 1 means errors, 2 means a missing or empty file. Fix every error, re-run until `ok` is true, and read the warnings. Run the script; do not edit it. Pass `--today YYYY-MM-DD` only to reproduce a past run.
8. **Deliver** the report, the source log, and the fixed summary below. Without Python, check by hand: every claim row has a source id and a quote found in that source's logged quote; every source id is used; every body paragraph has a `[C#]`; confidence is within 0 to 1.

## Report contract

Formats, with a full skeleton, are in [references/templates.md](references/templates.md). Required level-2 sections, in order: Question, Summary, Findings, Claim table, Contradictions, Gaps.

- Every paragraph and list item under Summary and Findings carries at least one `[C#]`. A paragraph that cannot cite is opinion: cut it or label it in Gaps.
- Summary states only what the claim table supports, in the confidence the table gives. Conflicting figures appear as a range or as two figures, never one.
- Claim table columns exactly: `claim_id | claim | source_ids | quote | confidence`. Contradictions columns exactly: `topic | claim_ids | resolution`. Source log columns exactly: `id | title | url | accessed | quote`.
- Gaps lists sub-questions without an adequate source, pages that could not be opened, and claims dropped below 0.25.

## Fixed summary to the user

```
Question and scope: <one line>
Sources: <n logged>, <n primary>; Claims: <n>; Contradictions: <n>, <n unresolved>
Checker: ok true/false, <n warnings and what they were>
Weakest points: <claims at or below 0.5 and why>
Not checked: <what was not opened, not verified independently, or out of scope>
```

## Limits

- The checker proves structure and traceability to the logged quotes. It cannot tell whether a quote supports the claim, whether the quote is genuine, or whether the page says it; that depends on step 3 being honest.
- The quote-in-source test compares text after lowercasing and collapsing whitespace and quote marks; a paraphrased quote fails by design.
- Confidence bands are working values, not calibrated probabilities.
- The URL check tests shape only, not that the page exists.
- Table cells cannot contain a bare `|`; escape it as `\|`.
- Not for legal, medical or financial conclusions: the output is a traceable evidence summary, not advice.
