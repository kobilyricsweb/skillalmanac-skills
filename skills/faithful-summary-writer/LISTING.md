# Listing page content: faithful-summary-writer

**One line:** Summarizes one document so every sentence traces to the source, then checks the summary for invented or altered facts.

## What it does

The skill gives an agent a seven-step procedure: fix the reader and decision, pick a length from a ratio table (executive 5%, standard 10-15%, detailed 20-30%), pick a structure (point-first, chronological, argument-evidence), mark the source items that must survive, draft with a source line tag on every sentence, save the clean summary and check it. A checker script compares `source.txt` with `summary.txt` and prints strict JSON: summary sentences with no supporting span (token overlap over 1 to 3 adjacent source sentences), numbers and capitalised names absent from the source, numbers that are altered rather than rounded, negation and hedge differences against the closest source sentence, the compression ratio against the target, verbatim copies of 16 words or more, and coverage of source headings and top keywords. A faithfulness contract in the skill forbids outside facts, hardened hedges and lost attribution.

## Capabilities

- `scripts/check_summary.py SOURCE SUMMARY [--target executive|standard|detailed|RATIO] [--tolerance X]`: JSON with `ok`, `ratio`, `unsupported_sentences[]`, `unsupported[]`, `altered_numbers[]`, `negation_flips[]`, `hedge_drops[]`, `copied_spans[]`, `coverage`, `warnings[]`
- A length table, a structure table and a repair table that says what to do for each JSON field
- A reference of structure templates, reporting-verb equivalences and common unfaithful moves
- A fixed closing report: length, structure, checker result, what was omitted, what was not checked

## When to use

You have one article, report, paper, transcript or set of call notes and say summarize this, TL;DR, executive summary, condense it, or shorten it without changing the facts, and the summary has to be correct, not just short.

## When not to use

Combining several sources (needs claim reconciliation), translation, meeting minutes with action items and owners, rewriting for style or tone, tracing each claim of an essay to its evidence in a table, and fact-checking against the outside world.

How it differs from neighbours: `natural-prose-editor` changes how text reads and keeps its length; this skill compresses and proves each sentence against the source. `meeting-notes-and-actions` extracts decisions and tasks; this one summarizes any single document. `claim-evidence-map` builds a claim-to-evidence table for an argument; this one produces a short summary with a mechanical check on it.

## Requirements

Python 3.9 or newer for the checker (standard library only). No network. Without Python the agent follows the manual check in step 6.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved model-written summary. What exists is the checker on saved fixtures (source: a 261-word library pilot report):

1. `python scripts/check_summary.py evals/fixtures/source_report.txt evals/fixtures/summary_good.txt --target 0.4`: `ok` true, ratio 0.4904, 6 of 6 sentences supported, no unsupported details, no altered numbers, keyword coverage 1.0, exit 0.
2. `python scripts/check_summary.py evals/fixtures/source_report.txt evals/fixtures/summary_bad.txt --target 0.4`: `ok` false, exit 1. It reports the invented name "Greenfield Foundation", `$45,000` (source `$48,200`) and `21 percent` (source `18 percent`) as altered numbers, the auditor sentence as a negation flip (the source says the pilot did not measure retention), the invented sentence "The pilot proved that evening hours work..." as unsupported (score 0.364), and an 18-word verbatim copy.

## Limits

- Finds mechanical failures only; a paraphrase that changes meaning, a wrong causal link or a swapped subject can pass.
- Thresholds are working values, not measured optima.
- Unit conversions, reformatted dates and derived totals are reported as altered or unsupported; written numbers in the summary are not checked.
- The negation check compares whole sentences and can flag a correct partial summary of a negated sentence.
- English only; very long sources should be split.

## Evidence

See `VERIFICATION.md`. In short: static lint passed, and the 7 script fixture cases pass with expected values checked by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a long report; the agent states the reader, picks the standard level and the point-first structure.
2. It drafts a summary with `[L12]`-style tags on every sentence, then saves the clean version.
3. `check_summary.py` flags one altered figure and one dropped hedge; the agent fixes both and re-runs to `ok: true`.
4. The final report lists what was omitted and what was not checked.

## FAQ seeds

- Does it prove the summary is correct? No. It catches mechanical failures; the report always says what was not checked.
- Does it need network access? No.
- Does it work on a PDF? The agent needs the plain text in a file; it saves it as `source.txt` first.
- Can it summarize several documents together? No; that is a different job.
- Will it keep my hedges and who-said-what? Yes, that is a rule in the contract and the checker flags dropped hedges and negation differences.
- How is it different from asking "summarize this accurately"? It adds a length table, a source tag per sentence, a checker and a fixed report. No comparison run has been done yet.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
