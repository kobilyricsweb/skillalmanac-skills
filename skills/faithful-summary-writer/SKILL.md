---
name: faithful-summary-writer
description: Writes an accurate summary of one document where every sentence traces to the source and nothing is added. Use when the user says summarize this, TL;DR, executive summary, condense, or shorten without changing facts. Picks length from a ratio table and structure by purpose, then runs a script that flags unsupported sentences, numbers and names missing from the source, altered or flipped figures, dropped hedges, copied passages and the ratio. Do not use for merging several sources, translation, meeting action items, style rewrites, or checking claims against the outside world.
license: Apache-2.0
compatibility: The checker needs Python 3.9 or newer, standard library only, and no network. Without Python, follow the manual check in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Faithful summary writer

A summary is a promise: everything in it is in the source, said with the source's certainty. Short is secondary. Write the summary from the source only, prove each sentence against a source span, then run the checker.

## Faithfulness contract

1. Every summary sentence rests on one to three adjacent source sentences. If you cannot name them, delete the sentence.
2. No outside facts, background, definitions, advice, evaluation or prediction. "This is good news" is yours, not the source's.
3. Numbers keep their unit, date and comparison base. Round only to fewer significant digits ("38,832" may become "about 39,000", never "38,000").
4. Hedges survive: may, might, suggests, appears, likely, estimated, reportedly. Never turn "suggests" into "shows" or "plans" into "will".
5. Attribution survives. "Reyes said X" is not "X". Keep who said what, and keep disagreement between people.
6. Negations and limits survive ("did not measure", "without a staffing plan"). A source caveat that would change the reader's decision is mandatory, even at the cost of length.
7. Where the source is silent or vague, the summary is silent or vague. Do not resolve contradictions inside the source: report both.

## Workflow

```
- [ ] 1 Save the source as source.txt; fix reader, decision, length
- [ ] 2 Pick structure
- [ ] 3 Mark the must-keep items
- [ ] 4 Draft with source line tags
- [ ] 5 Strip tags, save summary.txt
- [ ] 6 Run the checker and repair
- [ ] 7 Report
```

1. **Intake.** If the source exists only in chat or a PDF, write its plain text to `source.txt` (line numbers in the report refer to this file). Ask, or infer and state: who reads the summary and what they will decide with it. Pick the length from the table; default is standard.

| Level | Share of source words | Example, 1,000-word source | Reader |
|---|---|---|---|
| Executive | 5% (check band 3-7%) | 50 words | Decides whether to open the source |
| Standard | 10-15% | 100-150 words | Needs the findings and caveats |
| Detailed | 20-30% | 200-300 words | Will act on it without opening the source |

   Sources under 300 words: use sentence counts instead (executive 1, standard 2-3, detailed 4-5); the ratio band is unreliable there. Over 10,000 words: summarise per section first, then summarise the section summaries, and run the checker on each section against its own text.

2. **Structure.** Read [references/structure-and-verbs.md](references/structure-and-verbs.md) only for the template of the structure you pick.

| Source kind | Structure |
|---|---|
| Report, news, decision memo, results | Point-first: conclusion, key figures, caveats, next step |
| Call, interview, incident, minutes, timeline | Chronological: what happened in order, with the outcome last |
| Paper, opinion piece, proposal, legal argument | Argument-evidence: claim, strongest support, objections, limits |

3. **Mark must-keep items.** List from the source: the conclusion, every figure the conclusion depends on, every stated limit, every named decision-maker, every dissent. These get sentences before anything else is considered.
4. **Draft with tags.** Write each sentence followed by `[L<line>]` or `[L<line>-<line>]` source lines. A sentence with no tag is not allowed. Cut in this order: examples, background, repeated points, adjectives, secondary figures. Never cut by deleting a hedge or a caveat to save words.
5. **Save.** Remove the tags and write the clean summary to `summary.txt`. Keep the tagged draft for the report.
6. **Check and repair.**

```bash
python scripts/check_summary.py source.txt summary.txt --target standard
```

   `--target` is `executive`, `standard`, `detailed` or a ratio such as `0.1`. `--tolerance` (default 0.01) is the relative difference below which a changed number counts as rounding. Fix, then run again. At most three rounds; if failures remain, report them rather than hiding them.

| JSON field | Meaning | Action |
|---|---|---|
| `unsupported_sentences` with `status: unsupported` | Under 40% of the sentence's content words appear in any 1-3 adjacent source sentences | Find the source span or delete the sentence |
| same, `status: weak` | 40-60% overlap, or words scattered with no shared word pairs | Re-read the best source line; tighten to what it says |
| `unsupported` | A number, percent, amount, year, date or capitalised name not in the source | Remove it or restore the source's figure. Derived numbers (totals you calculated) land here: delete them or show the arithmetic outside the summary |
| `altered_numbers` | Near a source number but not a legitimate rounding (rounding counts only from a source figure of the same kind with 3 or more significant digits, to fewer digits; otherwise exact or within `--tolerance`), or a score pair such as `5-4` written `4-5` (`reason: pair_order_reversed`) | Use the source value |
| `negation_flips` | Negation differs from the closest source sentence | Read both sentences. A real flip is a failure. If you summarised only the non-negated half of a negated sentence, add the negated half |
| `hedge_drops` | Source sentence hedged, summary sentence not | Restore the hedge or justify in the report |
| `copied_spans` | 16 or more words verbatim | Paraphrase, or quote with attribution |
| `ratio`, `target.status` | Share of source words; within, too_long, too_short | Cut or add must-keep items |
| `coverage` | Source headings and top 10 repeated words absent from the summary | Prompts only: ask whether a missing item changes the conclusion. Generic headings ("Background") are often legitimately absent |

   `ok` is true only when there are no unsupported sentences, no unsupported details, no altered numbers and no negation flips. A true `ok` still means nothing about meaning: re-read each sentence against its tagged lines once more.

   Without Python: for each sentence check its tagged lines for every number, name, negation and hedge, count words, and confirm that the conclusion and the source's biggest caveat are present.
7. **Report** in this fixed shape, after the summary:

```
Length: <words> of <source words> (<ratio>), target <level>
Structure: <chosen> because <reason>
Checker: <ok true/false; remaining flags and why they stand>
Omitted: <source items left out that a reader might want, esp. caveats>
Not checked: <meaning of each sentence beyond tags; claims against the world>
```

## Scripts

- `scripts/check_summary.py SOURCE SUMMARY [--target T] [--tolerance X]`: run it. Prints one JSON object: `ok`, `source_words`, `summary_words`, `ratio`, `target{name,low,high,status}`, `sentences{total,scored,supported,weak,unsupported}`, `unsupported_sentences[]`, `unsupported[]` (kind, text, sentence, count), `altered_numbers[]`, `negation_flips[]`, `hedge_drops[]`, `copied_spans[]`, `coverage{}`, `warnings[]`, `limits`. Exit 0 when `ok`, 1 when not, 2 for a missing, empty or invalid input with a plain message on stderr. Do not edit it to make a check pass.

## Boundaries

- One source in, one summary out. Several sources need claim reconciliation, not this skill.
- Do not summarise material the user has no right to share onward, and do not present a summary as the source's own words or as an endorsement.
- A summary of a disputed or false document says what the document claims, attributed, and does not endorse it.

## Limits

- The checker finds mechanical failures: surface overlap, literal numbers and names, polarity words. It cannot see a paraphrase that changes meaning, a wrong causal link or a swapped subject.
- Thresholds (0.6 supported, 0.4 weak, 16-word copy, 1% rounding, 25% alteration window) are working values, not measured optima.
- Written numbers ("three") count as source numbers but are not checked in the summary. Unit conversions (0.46 to 46%), reformatted dates and derived totals are reported as unsupported or altered.
- Sentence-initial capitalised words are skipped unless they form a multi-word name or an acronym; names absent only at sentence start can slip through.
- The negation check compares whole sentences, so a correct partial summary of a negated sentence can be flagged. Heading coverage compares words, not topics.
- English only. Sources over a few thousand sentences run slowly; split them.
