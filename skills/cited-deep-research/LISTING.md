# Listing page content: cited-deep-research

**One line:** Runs research as an auditable procedure so every claim traces to a logged source and quote, then checks it by script.

## What it does

The skill fixes the order of a research job: decompose the question, plan sources by tier, read and log each source (URL, access date, verbatim quote), turn what was learned into a claim table (claim, source id, quote, confidence), triage contradictions, and write a report in which every paragraph cites claim ids. A checker script reads the finished report and the source log and prints strict JSON listing claims with no source, sources never used, missing or non-matching quotes, out-of-range confidence, uncited paragraphs, unknown ids and unresolved contradiction rows. A confidence scale and a conflict-triage order replace ad hoc judgement.

## Capabilities

- `scripts/validate_research.py REPORT SOURCES`: JSON with `ok`, `counts`, `errors`, `warnings`; exit 0, 1 or 2
- Defined Markdown formats for the source log, claim table and contradictions table, with a skeleton
- Confidence bands and a source-tier guide
- Fixed closing summary that names weakest points and what was not checked

## When to use

You ask for a sourced or cited research report, deep research with traceable claims, a source log with quotes, or you want an existing report checked for unsupported claims.

## When not to use

Quick factual answers; formatting references in APA, MLA or similar; market sizing and competitor work (the market-research skill in batch 01, `sourced-market-research`, covers that domain); plagiarism or AI-text checks; legal, medical or financial advice.

How it differs: this skill is domain-neutral and is about citation discipline, a fixed claim-table format and a validator. It does not choose what to research or supply domain methods. The nearest neighbours in the catalogue by name are `sourced-market-research` (market-specific) and `claim-evidence-map` and `decision-evidence-ledger` (batch 03); they were checked by name only, not read, so overlap in detail has not been compared.

## Requirements

Python 3.9 or newer for the checker (standard library only, no network). Reading sources needs whatever web or file access the agent already has. Without Python the agent applies the manual checks in step 8.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Saved fixture runs of the checker (fictional sources, `--today 2026-11-21`). No with-skill agent run exists yet, so no agent-written report is shown.

1. Good report:
   `python scripts/validate_research.py evals/fixtures/report_good.md evals/fixtures/sources_good.md --today 2026-11-21`
   Output: `"ok": true`, counts 4 sources, 5 claims, 1 contradiction, 0 errors, 0 warnings. Exit 0.
2. Deliberately broken report:
   `python scripts/validate_research.py evals/fixtures/report_bad.md evals/fixtures/sources_bad.md --today 2026-11-21`
   Output: `"ok": false`, 16 errors and 7 warnings, including `claim_no_source` (C2), `claim_unknown_source` (C3 cites S9), `claim_quote_not_in_source` (C4), `claim_quote_missing` (C5), `confidence_out_of_range` (C6 at 1.4), `paragraph_uncited`, `citation_unknown_claim` (C8), three `source_unused`, `source_date_future`, `source_url_invalid`, `section_missing` (Gaps), and a warning `single_source_high_confidence` (C7 at 0.95). Exit 1.

## Limits

- Proves structure and traceability to the logged quotes only; it cannot tell whether a quote supports a claim or whether the page really says it.
- Quote matching is case-, whitespace- and quote-mark-insensitive, and rejects paraphrases by design.
- Confidence bands are working values, not calibrated probabilities.
- The URL check is shape only.
- Not advice in legal, medical or financial matters.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN; 4 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: a research question plus a source pack; the agent decomposes it into sub-questions and logs sources with quotes.
2. The agent builds the claim table and notices two sources disagree; it adds a contradictions row with a stated reason.
3. First checker run shows an uncited paragraph and a source never used; the agent fixes both.
4. Second run prints `"ok": true`; the agent delivers the report and the fixed summary naming weakest claims.

## FAQ seeds

- Does it need network access? The script does not. Fetching sources uses whatever access the agent already has.
- Does it verify that my sources are true? No. It checks that every claim traces to a logged quote; truth of the source is judged by tier and confidence, by the agent and you.
- How is it different from asking an agent to "cite sources"? It fixes a log, a claim table and a checker, and the checker fails on uncited paragraphs, unused sources and quotes that do not match. No comparison run has been done yet.
- Can it check a report I wrote myself? Yes, if it is in the documented format; otherwise the agent converts it first.
- Does it work with APA or MLA citations? No; it uses claim ids. Formatting references is a different job.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## Differentiators and manual step (fix round 2026-11-21)

- Versus `claim-evidence-map` (claim table over evidence the user supplies) and `sourced-market-research`: this skill covers open-web research with a source log, claim table and validator. The installed generic deep-research skill has no fixed log or validator.
- The script cannot see contradictions the author did not list. Before delivering, compare every pair of claims on the same topic that carry different numbers, and list each conflict in the contradictions table.
