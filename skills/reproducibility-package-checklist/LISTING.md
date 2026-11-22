# Reproducibility package checklist

## One line

Reads a research project folder and reports which of nine rerun requirements (provenance, licence, versions, seeds, run order, entry command, expected outputs, environment, privacy) are missing, with a severity and a verdict.

## What it does

The skill works through a fixed ten-step procedure over a folder listing and the text of its README, dependency file, code and outputs. For each of the nine checks it records PASS, GAP or UNKNOWN, and for each gap it assigns critical, high, medium or low using a written severity table. The verdict follows from the worst gap found: any critical gap gives "Blocked", a high gap with no critical gap gives "Not ready", and only medium or low gaps give "Ready for a clean rerun test. Not yet confirmed." The skill never uses the word reproducible as a verdict. It returns a gap table, per-severity counts, a README skeleton with TODO markers where the folder gave no answer, and a list of what was not verified. It does not run code, install packages or download data.

## When to use

Use it before a researcher shares an analysis folder with a co-author, a reviewer or a journal, or after a rerun failed because a file, a package version or a seed was missing. It suits projects that mix Python and R scripts, plain CSV inputs and a few figures or summary tables, because its checks name the file and line where each gap sits.

## When not to use

Do not use it to judge whether a statistical method is appropriate or whether a conclusion follows from the data. Do not use it for licence interpretation beyond quoting the licence text it finds. Do not use it to certify a project as reproducible: only a clean rerun that the user confirms can do that.

## Requirements

No script, no network access and no special software. The agent needs to read text: a folder listing, and optionally the README, dependency file, code and output files. Any text-capable agent can follow the procedure.

## Example

Excerpt from the smoke run, the gap table for a described three-script project with a raw survey file containing an e-mail column:

```
### Verdict
Blocked: a rerun will probably fail or differ.

| # | Check | Status | Severity | Evidence | Fix |
|---|---|---|---|---|---|
| 1 | provenance | GAP | critical | data/raw/responses_2025.csv, responses_2024.csv: no source or retrieval date in README | Add source, retrieval date and collection method for each raw file. |
| 4 | seeds | GAP | critical | code/clean_data.py (10% row drop), code/analysis.R (sample() bootstrap): no seed set | Set and record a seed in both scripts. |
| 6 | entry command | GAP | critical | no Makefile, no entry script | Add one entry command that runs all steps. |
```

## Limits

The checks read text only. A file the listing names but the user did not paste cannot be inspected, so its checks are UNKNOWN rather than PASS. Working thresholds (8 GB memory, 1 hour runtime, relative tolerance 1e-6) are starting values chosen for this skill, not published standards, and a project with other needs should adjust them and say so in its README. The skill cannot detect a seed that is set in a file it was not shown, and it cannot tell whether a documented exclusion is complete.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
