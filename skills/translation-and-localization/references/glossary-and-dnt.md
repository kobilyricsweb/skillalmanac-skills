# Glossary and do-not-translate file

## Contents
- File format
- What goes where
- Building one when none exists

## File format

One JSON object, passed with `--glossary`:

```json
{
  "terms": {"Dashboard": "Tableau de bord", "Invoices": ["Factures", "Facturation"]},
  "do_not_translate": ["Acme Cloud", "OAuth"],
  "allow_identical": ["OK", "Email"],
  "allow_identical_keys": ["brand.name"]
}
```

- `terms`: source term to required target term. A list means any one of the listed forms is accepted. Matching on the source uses whole words, ignoring case, so `Invoices` does not fire on `Invoice`. List singular and plural separately if both occur. Matching in the target is a case-insensitive substring test.
- `do_not_translate`: strings that must appear unchanged (case-sensitive) in every target value whose source contains them.
- `allow_identical`: whole source values that may legitimately equal their translation (suppresses `untranslated_identical`).
- `allow_identical_keys`: the same exemption by key.

## What goes where

| Kind of text | Put it in |
|---|---|
| Product, company, plan and feature names; command, flag and API field names; file extensions; keyboard keys written as code | `do_not_translate` |
| Domain nouns the product uses as fixed UI vocabulary (Workspace, Invoice, Seat) | `terms` with the one approved translation |
| Words that are the same in the target language (Email in French, Hotel in German) | `allow_identical` |
| Generic words (Save, Cancel, Settings) | Not in the glossary unless the team has fixed them; consistency here is checked by reading the report, not by a rule |

A term with two meanings in the source (Post as noun and verb) needs two entries keyed by the context, or a human decision; the script cannot separate them.

## Building one when none exists

1. Read the source file and list every capitalised multi-word phrase, every word that appears in 5 or more strings, and every token inside backticks or code styling.
2. Propose the target term for each; mark which are product names (do not translate).
3. Show the list to the user and wait for approval when the project is customer-facing. Otherwise use it, and record it in the report under "Glossary".
4. Save it next to the target file so the next run reuses it.
