# Listing page content: natural-prose-editor

**One line:** Edits text to read like a careful person wrote it, keeping every number, name and claim.

## What it does

The skill gives an agent a seven-step edit procedure: scan, read for the author's voice, edit by pattern (delete padding first, then stock words, stacked hedges and template contrasts), re-read, re-scan and report. A scan script flags 13 documented pattern families and sentence-level signals (stacked hedges, runs of sentences with the same opener, uniform sentence length, frequent em dashes) with line numbers. A second command compares the original with the edit and lists any number, URL, quotation, inline code or name that went missing or appeared. A preserve-facts rule forbids changing claims or hardening a hedge.

## Capabilities

- `scripts/prose_scan.py scan`: JSON report of findings by line, counts by category, findings per 100 words, verdict clean, light or heavy
- `scripts/prose_scan.py facts`: JSON report of facts missing from or added to an edit
- A pattern guide with safe rewrite examples
- A fixed report: what changed, what was kept on purpose, facts check, what is left for the author, what was not checked

## When to use

You say humanize this, make it sound human, remove the AI tone, de-slop, tighten, or this reads like a bot wrote it, and the facts must stay put.

## When not to use

Translation, fact-checking, summarising, writing new text from nothing, or getting past AI-detector or plagiarism checks on graded or regulated work. The skill declines that last goal.

## Requirements

Python 3.9 or newer for the two scripts (standard library only). No network. Without Python the agent follows the pattern guide by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill run exists yet, so there is no saved edit to show. What exists is the scanner on the saved fixtures:

1. `python scripts/prose_scan.py scan evals/fixtures/ai_heavy.md`: 101 words, 21 findings, 20.79 per 100 words, verdict heavy, exit code 1 (stock words, an era opener, a template contrast, a stacked hedge, a closing offer).
2. `python scripts/prose_scan.py facts evals/fixtures/facts_original.md evals/fixtures/facts_edit_bad.md`: `ok` false; reports `$4.5`, `12`, the filing URL and a quotation missing, and `$5` added.

## Limits

- English surface patterns only; context-dependent tells are missed and honest uses of ordinary words can be flagged.
- Thresholds are working values, not measured optima.
- The facts check cannot see a claim reworded into a different claim.
- Short texts give noisy density figures.
- Tone and register are the author's; the skill does not change them.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 5 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a draft full of stock phrases; run `scan`: verdict heavy, line numbers shown.
2. The agent edits: deletions first, plain words, one hedge kept.
3. Run `scan` again (clean or light) and `facts` (`ok: true`).
4. Show the report, including what was left alone on purpose.

## FAQ seeds

- Will it change my numbers or quotes? The rule forbids it and the `facts` command checks it, but meaning changes inside a sentence are not detectable by the script.
- Will it get my text past AI detectors? That is not what it is for, and it declines that goal for graded or regulated work.
- Does it need network access? No.
- Does it flatten my voice? Step 3 identifies intentional style first, and the report lists what was kept on purpose. Efficacy on voice has not been measured.
- Does it work for other languages? The scan is English only.
- How is it different from a plain "rewrite this naturally" prompt? It adds a fixed order of edits, a facts check and a report. No comparison run has been done yet.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
