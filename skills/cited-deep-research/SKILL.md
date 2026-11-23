---
name: cited-deep-research
description: Runs a research task as an auditable procedure (source log with URL, access date and verbatim quote; claim table with source id, quote and confidence; contradiction table; report where every paragraph cites) and checks it with a stdlib script that outputs JSON. Use when the user wants a sourced or cited report, a literature review or evidence comparison with references, a source log, or an existing report fact-checked against its sources. Do not use for quick factual answers, one or two lookups, APA or MLA formatting, market sizing, or plagiarism checks.
license: Apache-2.0
compatibility: The checker script needs Python 3.9 or newer, standard library only. No network access is used by the script; reading sources needs whatever web or file access the agent already has. Without Python, follow the manual checks in step 7.
metadata:
  author: Skill Almanac Editorial
  version: "0.2.0"
  network: none
  license: Apache-2.0
  author_model: claude-sonnet-5-5
---

# Cited deep research

Every statement must point to a quote in a source you actually opened. The checker proves structure and quote traceability; honesty in step 3 is on you.

## Step 0: pick the size (stop early when you can)

- **Small job** (one or two facts, one source, or the user wants a short answer): answer plainly in the user's format with source and quote inline. No tables, no script.
- **No sources attached and no web or file access**: do not invent any. Say so in one line, list what you would need (named documents or URLs), and stop. Do not write URLs from memory.
- **Brief is ambiguous and the answer would change** (undefined product, region, period): ask at most 3 questions and stop. If you cannot ask, state the assumption in one line and go on.
- **User supplied a fixed layout, id set, count or word limit**: it overrides every template here. Follow it literally (exact columns, exact ids, every number asked for, the file names given).
- Otherwise run the full procedure below.

## Rules that never bend

1. Log a source only after opening it and reading the passage. Snippets are leads.
2. Copy the quote from the opened text; never recall it. One sentence.
3. No claim without source id and quote; otherwise it goes to Gaps.
4. Never average or smooth conflicting sources: record both.
5. Use only the supplied files for file-based tasks. Mark any self-computed figure as `derived` with its arithmetic. Drop files that do not bear on the question and say which in Gaps.
6. Never edit the checker to pass.

## Procedure

1. **Scope.** One-sentence question; time window, region, term definitions; 3 to 7 sub-questions (fewer for small topics), each with a done-condition.
2. **Sources.** Best first: originating document, independent analysis, reporting, commentary. Two articles repeating one press release are one source. Tiers: [references/sources-and-contradictions.md](references/sources-and-contradictions.md).
3. **Log.** One row per opened source in `sources.md`: `id | title | url | accessed | quote` (ids `S1..`, date `YYYY-MM-DD`). Dead or paywalled pages go in Gaps, never cited.
4. **Claims.** One row per atomic claim: `claim_id | claim | source_ids | quote | confidence`. Quote must be verbatim from that source's logged quote. Confidence: 0.85-1.0 primary plus independent agreement; 0.65-0.84 one primary or two independent secondary; 0.45-0.64 one secondary, a source with a stake, or a one-step inference; 0.25-0.44 hearsay (rumour only); under 0.25 Gaps. A single source above 0.8 needs a justification.
5. **Contradictions.** Compare by hand every pair on the same topic with different numbers or dates. Test in order: definition or population, date, method, source tier, copying. Table `topic | claim_ids | resolution`; `unresolved` shows both figures. Also note when two source types disagree (for example interviews vs survey) even if not asked.
6. **Report.** Sections in order: Question, Summary, Findings, Claim table, Contradictions, Gaps ([templates](references/templates.md)). Every paragraph and list item in Summary and Findings ends with `[C#]`. If the user asked for counts (for example "3 of 6 interviews"), state each count in the text and cite the ids exactly as the user defined the set; do not add other source types to that id set.
7. **Check.**

```bash
python scripts/validate_research.py report.md sources.md [--reply reply.txt --max-words N]
```

   JSON `ok/counts/errors/warnings`; exit 0 ok, 1 errors, 2 missing file. Fix and re-run until ok. `--reply` counts the words of your chat reply against the user's limit; trim the reply, never the evidence. Without Python: check by hand that each claim has an id and a quote found in its source, each source is used, each paragraph has `[C#]`.
8. **Reply**, within any word limit (the summary below is the maximum; shrink it to fit):

```
Scope: <one line>
Sources <n> (<n primary>); claims <n>; contradictions <n> (<n unresolved>)
Checker: ok true/false, warnings <n>
Weakest: <claims at or below 0.5, why>
Not checked: <unopened, unverified, out of scope>
```

## Limits

Checker cannot tell if a quote supports the claim or is genuine; paraphrased quotes fail by design; URL check is shape only; escape `|` in cells as `\|`. Evidence summary only, not legal, medical or financial advice.
