# Input format and finding codes

## `format` input (JSON, UTF-8, at most 2 MB, nesting at most 12, integers at most 15 digits; write decimals as strings)

```
{ "entries": [ {entry}, ... ],
  "citations": [ ["id1"], ["id2","id3","id4"], {"ids":["id1"],"narrative":true},
                 {"ids":[{"id":"id2","locator":"pp. 5-10"}]} ] }
```

`citations` is the in-text citations in manuscript order. Numbers are given in order of first citation. Entries never cited are left out of the list with a warning.

Common entry keys: `id` (unique), `type` (`journal`, `book`, `chapter`, `conference`, `web`), `authors` (list of `{"given","family","suffix"}` or `{"org"}`), `title`, `year` (four digits), `month` (number, name, abbreviation, or two joined by `/`), `day`, `doi` (bare, `doi:` or doi.org form), `url`.

| Type | Keys |
|---|---|
| `journal` | `journal`, `journal_abbrev`, `volume`, `issue`, `pages`, `article_number`, `early_access` (true, needs month, day, year), `status` (`to_be_published` or `submitted`) |
| `book` | `edition` (number or 2nd), `city`, `state`, `country`, `publisher`, `chapter_number`, `pages` |
| `chapter` | `book_title`, `editors`, `city`, `state`, `country`, `publisher`, `chapter_number`, `pages` |
| `conference` | `conference` (abbreviated name as printed), `city`, `state`, `country`, `month`, `days` (such as `20-22`), `pages`, `paper`, `presented` (true for an unpublished talk) |
| `web` | `website`, `url`, `accessed` (`{"month","day","year"}`), plus optional publication `month`, `day`, `year` |

Output (stdout, strict JSON, ASCII-escaped): `schema_version`, `tool`, `mode`, `source`, `ascii`, `in_text` (`citation`, `text`, `numbers`), `references` (`number`, `id`, `text`), `issues`, `summary` (`citations`, `references`, `errors`, `warnings`, `verdict`). `--ascii` prints straight quotes and hyphens for page ranges. `--text-out` writes `[n] text` lines to a new file.

## `verify` input

A text file of lines starting with `[n] `; a line that does not start that way continues the previous reference. `--manuscript` is a text file whose bracketed numbers are checked against the list.

Output: `schema_version`, `tool`, `mode`, `source`, `issues`, `first_appearance_order`, `summary` (`references`, `errors`, `warnings`, `verdict`). Each issue has `severity`, `code`, `ref` (reference number or null) and `message`.

## Finding codes

| Code | Severity | Mode | Meaning (rule in ieee-rules.md) |
|---|---|---|---|
| `missing_field` | error | format | a required field is absent |
| `bad_month`, `bad_year`, `bad_date`, `bad_pages`, `elided_pages`, `bad_doi`, `bad_url`, `bad_edition` | error | format | value not understood; elided pages such as 2787-93 are refused, not expanded |
| `uncited_entry` | warning | format | not cited, so not listed |
| `possible_duplicate_source` | warning | format | same DOI or title and year under two ids |
| `journal_abbreviation_missing` | warning | format | full title printed, supply `journal_abbrev` |
| `missing_volume`, `missing_location`, `us_state_missing`, `state_ignored`, `author_given_name_missing`, `hyphenated_given_name`, `article_id_moved`, `url_dropped`, `doi_ignored`, `edition_ignored`, `fields_ignored`, `publisher_unabbreviated`, `conference_name_unabbreviated`, `ordinal_not_numeric` | warning | format | see message |
| `author_surname_first`, `more_than_six_authors`, `et_al_period`, `et_al_with_several_names`, `comma_before_suffix` | error | verify | name rules |
| `given_name_spelled_out`, `usa_form`, `us_state_form`, `conference_name_unabbreviated`, `ordinal_not_numeric` | warning | verify | pattern-based, check by eye |
| `comma_outside_quote`, `missing_final_period`, `url_trailing_period`, `no_year` | error | verify | punctuation and date |
| `month_not_abbreviated`, `month_missing_period`, `label_format`, `pp_for_single_page`, `p_for_page_range`, `article_id_in_page_slot`, `to_appear_in`, `doi_format`, `online_available_format`, `accessed_format`, `edition_format` | error | verify | format of labels, months, DOI, online items |
| `duplicate_number`, `number_sequence`, `duplicate_reference`, `stray_text` | error, error, warning, warning | verify | list integrity |
| `range_dash`, `first_citation_order`, `cited_not_in_list` | error | verify (manuscript) | in-text numbering |
| `combined_numbers_in_bracket`, `listed_not_cited` | warning | verify (manuscript) | `[1, 2]` written in one bracket; list entry never cited |

Source for the rules behind the codes: IEEE Reference Style Guide for Authors, V 3.28.2025, https://docs.google.com/document/d/1j1L96U2NagwWI9MEVDNVKt9pXxRzTH7h3krI3Mb6wZE, read 2026-11-24. `combined_numbers_in_bracket` is a warning because the guide shows separate brackets but does not forbid a combined one in so many words.
