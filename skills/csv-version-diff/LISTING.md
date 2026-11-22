# Listing page content: csv-version-diff

**One line:** Compares two versions of a CSV by key and lists added, removed and changed rows, cell by cell.

## What it does

The agent confirms a key column with you (it never matches rows by position), then runs a script that reads both files, handles BOMs, odd delimiters and encodings, infers column types and matches rows by key. The result is strict JSON: schema changes (columns added, removed, type drift, rename questions), counts of added, removed and changed rows, changed cells per column with examples, and warnings about duplicate or blank keys, reformatted keys, row-count swings and null-rate jumps. Tolerances (absolute, relative, trim, ignore case) are off until you ask for them. An optional Markdown report carries the same sections.

## Capabilities

- Added, removed, changed and unchanged row counts by key, with up to N examples per column
- Per-cell old value, new value and numeric delta; formatting-only differences ("5.00" and "5.0") counted apart from real changes
- Column added, removed, reordered and type-changed detection; a rename proposed only as a question (same value in at least 90 percent of matched rows)
- Warnings for duplicate keys, blank keys, keys that changed format (004 to 4), delimiter or encoding differences, row-count shifts over 20 percent
- `--suggest-keys` lists columns that are filled and unique in both files
- JSON on stdout; optional `--out` and `--markdown` files that can never overwrite an input

## When to use

You have the old and the new export of the same table and need to know exactly what changed: "diff these two CSVs", "what changed since last month", "which rows disappeared".

## When not to use

Profiling one file, clustering duplicate records, auditing a data contract, checking train/test leakage, merging files, or diffing text and code. Those belong to other skills.

## How it differs from nearby skills

`data-analysis-eda` and `dataset-field-profiler` describe one file; `duplicate-record-triage` clusters duplicates inside one file; `record-contract-audit` checks rows against a stated contract; `split-leakage-check` looks for rows shared between splits. This skill compares two versions of one table by key.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows a manual comparison routine and says so.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from saved fixture runs of the script, not from an agent session (no with-skill agent run exists yet).

1. `python scripts/csv_version_diff.py evals/fixtures/orders_old.csv evals/fixtures/orders_new.csv --key order_id`: exit 1, verdict `differences`; 1 row added (1006), 1 removed (1005), 3 changed of 4 common; `ship_date` and `status` removed, `state` and `region` added; `status` to `state` proposed as a rename (4 of 4 values equal); `qty` changed type from int to text because 1006 holds `n/a`; price `5.00` to `5.0` counted as format-only.
2. Same pair with `--abs-tol 0.01 --trim`: 1 row changed instead of 3, because the 0.004 price difference is within tolerance and the trailing space in `Delta ` is normalised; both counted in `within_tolerance_cells` and `normalised_cells`.

## Limits

- Both files are read fully into memory.
- Dates are recognised by shape and compared as text.
- Rows with duplicate or blank keys are excluded and counted, so a "no changes" verdict can be incomplete (`complete: false`).
- Rename detection needs at least 3 matched non-blank rows and unedited values.
- It reports differences, not whether a difference is correct.

## Evidence

See `VERIFICATION.md`. In short: lint passed with 0 FAIL and 0 WARN, and the 16 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: "Here is last week's orders export and this week's, order_id is the key, what changed?"
2. The agent runs the script; the warnings and counts appear.
3. The agent asks whether `status` became `state`, and flags the `n/a` in `qty`.
4. It reports changed cells by column, and writes `report.md` to a new path.

## FAQ seeds

- Does it need network access? No.
- What if I do not know the key? The agent runs `--suggest-keys` and asks you; it will not compare by row position.
- Can it overwrite my original CSV? No. It refuses any report path that is the same file as an input, even with `--force`.
- How are rounding differences handled? Only if you ask: `--abs-tol` or `--rel-tol`. Numbers that differ only in spelling ("5.00", "5.0") are counted separately as format-only.
- Will it tell me a column was renamed? It proposes it as a question when values match in 90 percent of rows; it never applies it silently.
- What data leaves my machine? None; the script has no network or subprocess code.
- How do I uninstall? Delete the skill folder.

## Changelog

- 0.1.0 (2026-11-21): first draft; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
