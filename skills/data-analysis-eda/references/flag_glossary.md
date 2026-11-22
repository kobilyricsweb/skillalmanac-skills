## Contents

- How to read a flag
- Column flags
- File-level lists
- Target checks

# Flag glossary for eda_profile.py output

Read only the entries for flags that appear in the JSON you are working with.

## How to read a flag

A flag is a question for the analyst, not a verdict. Each entry gives the rule the script uses, the usual cause, what to check next, and how to word it in a finding.

## Column flags

| Flag | Script rule | Usual cause | Check | Wording |
|---|---|---|---|---|
| `constant` | one distinct non-missing value | export default, filtered extract | does it vary in the full source? | "has one value in this file" |
| `near_constant` | top value is 99% or more of non-missing | rare-event flag, or a column that was mostly never filled | count and rows of the rare value | "99.x% of rows are X; N rows differ" |
| `all_missing` | no non-missing value | column never populated | which tokens were counted (`missing_tokens`) | "contains no values" |
| `likely_id` | unique and at least 20 rows, or id-like name with 50% or more distinct values; `id_confidence` high, medium | row key | is it the entity key or only the row key? | "looks like a row identifier" |
| `possible_id` | unique integers without an id-like name (`id_confidence` low) | a measure with no repeats, such as a total | read the name and range | usually not a key; do not exclude from analysis automatically |
| `repeating_key` | id-like name, under 50% distinct | join key (customer_id repeated per order) | rows per key distribution | "keys repeat: unit of analysis is not the key" |
| `mixed_types` | no single type reaches 95% of non-missing | free-form entry, units in cells ("12kg") | `kind_counts`, `non_numeric_values.examples` | "holds both numbers and text" |
| `non_numeric_in_numeric` | numeric column with some text | stray tokens such as "unknown", "TBD" | `non_numeric_values.examples` | "N values are text in a numeric column" |
| `sentinel_suspect` | -9, -99, -999, -9999, -99999, 99, 999, 9999, 99999 or 999999 is the column min or max and has 3+ rows and 0.5%+ share | missing-value codes from an old system | `sentinel_suspects`, distribution with and without | "N rows hold 999, which looks like a missing-value code" |
| `extreme_outliers` | any value beyond 3 times the interquartile range from the quartiles | real extremes, unit errors, sentinels | rows themselves; `p95` against `max` | "N values lie beyond 3 IQR; owner should confirm" |
| `binary_01` | integer column holding only 0 and 1 | yes/no flag | treat as boolean, not as a quantity | "is a 0/1 flag" |
| `possible_year` | integer, name contains year or yr, range 1800-2100 | year stored as number | do not average it | "holds calendar years" |
| `formatted_numbers` | values like `$1,200`, `45%` parsed as numbers | spreadsheet export | the parsed value excludes the symbol | "numbers carry currency or percent symbols" |
| `zero_padded_codes` | digit strings with leading zeros (`02134`) | zip, product or account codes | never convert to integer | "codes with leading zeros, kept as text" |
| `long_digit_strings` | integers over 15 digits | account numbers, ids | float precision would corrupt them | "long digit strings, kept as text" |
| `whitespace_padded` | leading or trailing spaces (`whitespace_padded_values` counts them) | manual entry | stripped before counting | "N values had stray spaces" |
| `case_variants` | values equal after lower-casing and space collapse (`case_variant_groups`) | inconsistent entry | examples listed | "same category spelled N ways" |
| `high_cardinality_string` | strings, 90% or more distinct, at least 20 rows | names, emails, free text | do not tabulate | "mostly unique text" |
| `likely_free_text` | unique strings with mean length over 40 | comments | not an id | "free text" |
| `date_order_ambiguous` | every value parses as both day-first and month-first | slash dates with day and month at most 12 | `alt_range_if_day_first` | "range is X-Y if month-first, X2-Y2 if day-first; owner to confirm" |

## File-level lists

| Key | Meaning | What to do |
|---|---|---|
| `bad_rows` | rows with the wrong field count or a parse error, excluded | read `first_examples`; a block of consecutive lines suggests a broken export or wrong delimiter |
| `duplicate_rows` | exact repeats of an earlier row | report the count; do not remove without the owner's say |
| `missing_over_20_pct` | columns at 20% missing or more | stage 4 group comparison |
| `near_duplicate_numeric_pairs` | absolute Pearson r of 0.9 or more on sampled rows | redundant or derived columns (one is a multiple of the other) |
| `date_columns` | detected date columns with min, max, `row_order` | stage 7; `unsorted` means sort first |
| `warnings` | encoding fallback, renamed headers, NUL removal, truncation, unbalanced-quote hint | repeat each one in the report |

## Target checks

`target.leakage_candidates` entries have `check` of `numeric_correlation` (absolute r of 0.95 or more with a numeric outcome) or `category_purity` (the share of rows whose value maps to the most common outcome class for that value; 0.99 or more and at least 3 points above the majority-class share). A missing cell is treated as a value, so a column filled in only after the outcome is caught. A hit means "could not have been known in advance or restates the outcome" until the owner says otherwise; it is not proof. Absence of a hit means nothing about leakage that works through combinations of columns.
