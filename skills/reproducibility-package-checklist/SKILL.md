---
name: "reproducibility-package-checklist"
description: "Checks whether a research project folder holds what a stranger needs to rerun an analysis: data provenance and licence, pinned software versions, random seeds, run order, entry command, expected outputs, environment notes and privacy exclusions. Use when a researcher asks if an analysis can be rerun, before sharing code or data with reviewers, or after a failed rerun. Do not use for judging whether the methods or conclusions are correct, for legal licence advice, or for declaring a project reproducible without a clean rerun confirmed by the user."
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Reproducibility package checklist

Use this procedure to check a research project folder for the things a stranger needs to rerun it. The output is a gap table and a verdict on readiness. It is not a judgement of the science. Work only from the folder listing and the file contents the user supplies. Do not run the project code, install packages or fetch data.

## Inputs

- Folder listing with file names and sizes where known. Required.
- Optional, read when supplied: README, dependency file (requirements.txt, pyproject.toml, lock file, renv.lock, environment.yml), code files, configuration files, output files.
- Project name, used in the report title.

If the folder listing is missing, stop (see the refuse list).

## Workflow

1. Inventory. List every file and group it as raw data, derived data, code, configuration, output, documentation or other. Output: an inventory table with columns File, Group, Note. Mark files whose names suggest reported results (figure, table, result, summary).

2. Data provenance and licence. For each raw input or external data source, find its origin, retrieval date and licence or terms of use. Output: one provenance row per input. An input with no stated origin is a critical gap. Shared data with no licence or terms file is a high gap.

3. Software versions. Find the dependency file and the language version. Every package needs an exact version (for example pandas==2.1.4, not pandas). Output: one row stating the language version and the count of unpinned packages. No dependency file is a critical gap. Any unpinned package is a high gap.

4. Random seeds. Search code and configuration for randomness: random, numpy random, torch, sample(), shuffle, bootstrap, train/test split, simulation, random_state. Each use must have a seed set in code or config, and the seed value must be written down. Output: a list of randomness uses with file, line and seed status. Unseeded randomness that feeds a reported number is a critical gap. Unseeded randomness that does not feed a reported number is a medium gap.

5. Run order and entry command. Identify one command that runs the whole analysis from raw data to outputs (a single entry script, a Makefile target or a documented wrapper). If more than one script is needed, the order must be written down. Output: the entry command as stated, or NONE. No entry command is a critical gap. Two or more steps with no written order is a high gap.

6. Expected outputs. For each reported result (figure, table, headline number in text) record an expected value or the SHA-256 of the output file, plus the tolerance used to compare. Working values: integer counts must match exactly; decimal values match within relative tolerance 1e-6; figure files are checked by a written description only, because image bytes vary between machines. No expected values for any reported number is a high gap. No expected values for figures or tables only is a medium gap.

7. Environment notes. Record the operating system the project was run on, hardware needs (GPU yes or no, memory, runtime), and any external service or API key needed (name only, never the value). Working thresholds for stating hardware needs: memory above 8 GB or runtime above 1 hour. Missing environment notes are a medium gap. A required external service that is not documented is a high gap.

8. Privacy exclusions. Check whether the data contains personal identifiers (names, e-mail addresses, phone numbers, IP addresses, precise locations) or unpublished material, and whether a note says what was removed or masked and why. Personal fields with no exclusion note are a critical gap. Credential-like values found in files are a critical gap: name the file and line only and never repeat the value in the report.

9. Severity and verdict. Assign each gap a severity from the table below, then set the verdict using the verdict rules. Do not add gaps that the evidence does not support. If a check cannot be decided because its file was not supplied, record status UNKNOWN, not GAP.

10. README skeleton. Fill the skeleton in the output contract with what the folder shows. Mark every field you cannot fill as TODO. Do not invent versions, seeds, hashes or tolerances.

## Severity table (working values)

| Severity | Use when | Blocks rerun |
|---|---|---|
| critical | No entry command; no dependency file; unseeded randomness feeding a reported number; input with no origin; personal fields with no exclusion note; credential-like value in a file | yes |
| high | Any unpinned package; shared data with no licence or terms; two or more steps with no written order; undocumented external service; no expected values for reported numbers in text | no, but blocks Ready |
| medium | No expected values for figures or tables; no environment notes; no hardware needs; unseeded randomness not feeding a reported number | no |
| low | Naming inconsistency; undocumented optional output; missing file size | no |

## Verdict rules (apply in order, first match wins)

| Condition | Verdict line |
|---|---|
| Any critical gap | Blocked: a rerun will probably fail or differ. |
| No critical, at least one high gap | Not ready: fix the high gaps, then run a clean rerun. |
| Only medium or low gaps | Ready for a clean rerun test. Not yet confirmed. |
| No gaps | No gaps in this checklist. Reproducibility still needs a clean rerun confirmed by the user. |

The word "reproducible" is never used as a verdict.

## Output contract

Use these headings in this order.

### Verdict
One line from the verdict rules.

### Gap table
Columns, in this fixed order: `# | Check | Status | Severity | Evidence | Fix`.
Nine rows, one per check, in this order: provenance, licence, versions, seeds, run order, entry command, expected outputs, environment, privacy exclusions.
Status is PASS, GAP or UNKNOWN. Severity is critical, high, medium, low or a dash for PASS. Evidence is a file name and line number where applicable. Fix is one action of 15 words or fewer.

### Counts
One line: `Critical: n. High: n. Medium: n. Low: n. UNKNOWN: n.`

### README skeleton
A fenced block with these headings in order: Title, What this reproduces, Data (source, licence, access), Environment (operating system, language version, dependency file), Run (single entry command), Order (only if more than one step), Seeds, Expected outputs (file, value or hash, tolerance), Privacy exclusions, Known limits. Each field holds its found value or TODO.

### Not verified
Bulleted list. Always include: "No clean rerun was performed." and "Scientific correctness was not assessed." Add one bullet for each file the listing did not include that a check needed.

## Refuse / stop when

- The user asks you to state that the project is reproducible without a clean rerun that the user has confirmed.
- No folder listing or file contents are supplied. Stop and ask for the listing.
- The user asks you to run the code, install packages or download data. This procedure works only on supplied text.
- The user asks you to include raw personal data in the package. Refuse to add it and report it as a critical gap.
- The user asks for a legal opinion on a licence. Quote the licence text found and stop there.
