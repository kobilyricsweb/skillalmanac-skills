# Output fields and CSV facts

## Contents

1. Field reference
2. Verdict rules
3. Exit codes
4. Format facts the script relies on

## 1. Field reference

| Path | Type | Meaning |
|---|---|---|
| `verdict` | string | see section 2 |
| `complete` | bool | false when any row was excluded (duplicate, blank or ambiguous key) |
| `inputs.old` / `inputs.new` | object | `path`, `encoding` (utf-8, utf-16, cp1252, latin-1), `bom`, `delimiter`, `rows` (data rows read), `columns` |
| `key` | array | key columns exactly as given |
| `options` | object | `abs_tol`, `rel_tol`, `trim`, `ignore_case`, `null_tokens` |
| `schema_changes[].class` | string | `column_added`, `column_removed`, `renamed_candidate`, `type_changed`, `column_order_changed` |
| `schema_changes[]` (added or removed) | | `possible_rename_from` or `possible_rename_to`: column names proposed by the rename rule, empty when none |
| `schema_changes[]` (renamed_candidate) | | `from`, `to`, `match_share`, `rows_compared`, `name_differs_only_by_case`, `question` |
| `schema_changes[]` (type_changed) | | `from`, `to`, `direction` (`widened` int to float, `to_text`, `from_text`, `other`), `new_values_not_fitting_old_type[]` with `line` and `value` |
| `rows.excluded_old` / `excluded_new` | int | rows read but not diffed (duplicate, blank or ambiguous key) |
| `rows.common` | int | keys present in both files and compared |
| `rows.changed` | int | common keys with at least one changed non-key cell |
| `rows.cell_changes` | int | total changed cells over all columns |
| `rows.order_changed` | bool | the relative order of common keys differs between files |
| `column_change_counts.<col>` | object | one entry per shared non-key column: `changed_cells`, `format_only_cells`, `within_tolerance_cells`, `normalised_cells`, `null_to_value`, `value_to_null`, `whitespace_or_case_only` (a subset of changed), `numeric_changes`, and `max_abs_delta` when a numeric change exists |
| `column_summary[]` | array | per column: `status` (common, removed, added), `is_key`, `old_type`, `new_type`, `old_null_rate`, `new_null_rate`, `changed_cells` |
| `examples[]` | array | `kind`, `key` (object), and for a changed cell `column`, `old`, `new`, optional `delta` (new minus old) and `note`; values are cut at 200 characters |
| `warnings[]` | array | `code`, `detail`, plus code-specific fields such as `count`, `examples`, `lines` |

Inferred types: `int`, `float`, `date`, `text`, `empty` (no non-missing values). A column with a single non-numeric value among numbers is `text`; the types of individual cells are summarised by `type_counts` only inside the script, so check `new_values_not_fitting_old_type` for the offending values.

## 2. Verdict rules

- `differences`: any column added, removed or type-changed, any row added or removed, or any changed cell.
- `order_only`: none of the above, but row order or column order differs.
- `equivalent`: no change after the active options, but some cells were format-only, within tolerance or normalised. Report those counts.
- `identical`: nothing differs at all.

## 3. Exit codes

0 for `identical` and `equivalent`; 1 for `differences` and `order_only`; 2 for any usage or input error (no key, key column missing, unreadable or empty file, refused output path).

## 4. Format facts the script relies on

Background facts, restated in the author's words from general knowledge of these sources (not re-fetched while authoring; check them before relying on them in a published page):

- RFC 4180 (https://www.rfc-editor.org/rfc/rfc4180) describes the common CSV layout: optional header row, fields containing the separator, quotes or line breaks wrapped in double quotes, a literal quote written as two quotes. It is informational, so real files vary; hence the delimiter and encoding sniffing and the warnings.
- Python's csv module documentation (https://docs.python.org/3/library/csv.html) states that a reader must be given a file opened with newline handling left to the module, because quoted cells may contain line breaks; the script therefore decodes the bytes itself and passes a string buffer.
- A byte-order mark is the three bytes EF BB BF at the start of a UTF-8 file. Spreadsheet tools sometimes add it, and an unremoved one glues an invisible character onto the first header name, which makes the first column look renamed. The script strips it and warns.
- Spreadsheet tools commonly drop leading zeros from codes and identifiers when a file is opened and saved again. That is why a key such as 004 turning into 4 is reported as `key_format_drift` rather than as one removed and one added row.
