# Ticket file formats

Read this when writing or repairing a tickets file for `scripts/tickets_lint.py`.

## Contents
- Markdown format
- JSON format
- Size values
- What the report contains

## Markdown format

One level-2 heading per ticket: `## <id>: <title>`. The id is letters and digits with an optional hyphen (`T1`, `PAY-12`). Text before the first `##` heading is ignored, as are fenced code blocks. Fields follow as `Field: value` lines, optionally prefixed with `- ` or wrapped in bold. List fields take bullet or numbered items on the lines below.

Recognised fields (case-insensitive): `Outcome`, `Size` (or `Estimate`), `Depends on` (or `Blocked by`), `Non-goals` (or `Out of scope`), `Acceptance criteria`, `Definition of done` (or `DoD`). Depends-on values are ids separated by commas or spaces; `none` is allowed. Any line that is not a recognised field belongs to the field above it.

A heading without an id (`## Login stuff`) is an error, because ids are what dependencies refer to.

## JSON format

Either a list of ticket objects or `{"tickets": [...]}`. Keys: `id`, `title`, `outcome`, `size` (string or number), `depends_on` (list of ids), `non_goals` (list), `acceptance_criteria` (list of strings), `definition_of_done` (list). camelCase spellings of the multi-word keys are accepted. A wrong type is reported as `bad-field-type`.

## Size values

`XS` 0.5 day, `S` 1, `M` 3, `L` 8, `XL` 13, or a number (optionally followed by `d` or `days`) meaning one engineer's ideal days. The default limit is 3 days, changed with `--max-size-days`. Anything else is `bad-size`; an empty size is `missing-size`.

## What the report contains

Top level keys: `tool`, `version`, `file`, `format`, `ok`, `limits`, `ticket_count`, `errors`, `warnings`, `findings`, `build_order`. A file that cannot be read or parsed gives `ok` false and an `input_error` string, with exit code 2. Findings from Markdown input carry the heading's `line`.
