---
name: translation-and-localization
description: Translates and reviews product UI strings and docs between languages with glossary enforcement, protected placeholders ({name}, %s, ICU plural and select), length limits, do-not-translate terms, RTL and locale-format notes, and a script that compares a source and a target locale file (JSON or .properties) and prints strict JSON. Use when the user asks to translate or localize a locale file, i18n strings, app copy or a help page, review or QA a translation, check missing keys or broken placeholders, or keep terminology consistent across languages. Do not use for subtitles, certified or legal translation, live interpreting, or deciding which markets to enter.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual QA list in step 6.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Translation and localization

Translate strings so the product still works: every variable survives, every term is the approved one, every string fits its slot. Fluency is the easy part; the failures that reach users are broken placeholders, drifting terminology and overflowing buttons.

## Inputs to collect first

1. Source file and source locale, target locale (use a BCP 47 tag: `pt-BR`, `zh-Hant`, `ar`).
2. Glossary, if one exists. If not, build one in step 2.
3. Hard length limits per key (a map `key -> max characters`), if the UI has fixed slots.
4. Register: formal or informal address, if the language distinguishes it (German Sie/du, French vous/tu, Japanese keigo level). Ask once; never switch mid-file.

## Workflow

```
- [ ] 1 Read the source file and classify strings
- [ ] 2 Fix the glossary and do-not-translate list
- [ ] 3 Translate into a new target file, same keys
- [ ] 4 Run the comparison script
- [ ] 5 Fix every error, review each warning
- [ ] 6 Manual QA of what the script cannot see
- [ ] 7 Report
```

1. **Classify.** Mark strings that carry ICU (`{n, plural, ...}`), printf (`%s`, `%1$d`), named (`{name}`, `{{name}}`, `${x}`) or markup (`<b>`, `<0>`) tokens, and strings that are short UI labels (under 20 characters). These get the strict rules below. Never rename, add or drop keys; the target has exactly the source's keys.
2. **Glossary.** Use [references/glossary-and-dnt.md](references/glossary-and-dnt.md) for the file format and what belongs in it. Product names, command names, API fields, file extensions and legal entity names go into `do_not_translate`. Fix a single target term per source term before translating line one; one term, one translation, everywhere.
3. **Translate** into `<target>.json` or `<target>.properties` in the same format as the source. Rules in the next section.
4. **Compare**, with the glossary and limits when you have them:

```bash
python scripts/locale_check.py SOURCE TARGET --glossary glossary.json --limits limits.json
```

5. **Fix.** Work through `issues` in the JSON. All `error` items are fixed, not argued with; each `warning` is either fixed or explained in the report. Re-run until `"errors": 0`. Do not edit the script or the thresholds to make a check pass.
6. **Manual QA** (the script cannot see these): plural categories complete for the target language; word order of positional arguments reads naturally; dates, numbers and currency are formatted by the formatter and not typed into the string; RTL handling; consistent register; no mixed scripts by accident; sentence fragments that were joined in code still join. Details in [references/plural-rtl-locale.md](references/plural-rtl-locale.md): read only the section for the target language family.
7. **Report** in the fixed shape at the end.

## Translation rules that decide outcomes

| Situation | Rule |
|---|---|
| `{name}`, `{0}`, `{{name}}`, `${x}`, `%s`, `%(n)s` | Copy the token byte for byte. Never translate the name inside it, never add spaces inside it, never change the count. Word order around it may change. |
| printf positional args | If the target word order needs reordering, switch every argument in that string to the `%1$s`, `%2$d` form. Mixing numbered and unnumbered is a defect. |
| ICU `plural` | Keep the argument name and the `other` branch. Write the categories the **target language** needs, not the source's (see reference). Keep `#`. Do not translate selectors (`one`, `other`, `=0`). |
| ICU `select` | Selector words (`male`, `female`, `other`) are keys: do not translate them; keep every branch the source has. |
| Markup tags | Same tags, same count, same nesting order; translate only the text between them. Keep attributes (`href`) unchanged. |
| ICU apostrophes | In ICU strings an apostrophe before `{` starts a quote. French and Italian text next to a placeholder needs `''` for a literal apostrophe, or the placeholder disappears at runtime. |
| Do-not-translate term | Keep it exactly, including case. Inflected languages add case endings outside the term, not inside it. |
| UI label (under 20 source characters) | Use the shortest natural wording; an abbreviation is allowed only if the glossary lists it. |
| Identical to source | Allowed for brand names, codes and borrowed words the glossary lists in `allow_identical`; otherwise translate. |
| Emoji, URLs, email addresses, code spans | Unchanged. |
| Source is ambiguous (`"Post"`, `"Open"`, `"Back"`) | Do not guess: list the key under "Needs context" in the report. |

## Length limits

The script reports `length_ratio_exceeded` as a warning when the target is longer than the source by more than these ceilings (target characters divided by source characters):

| Source length (characters) | Ceiling |
|---|---|
| 1 to 10 | 3.0 |
| 11 to 20 | 2.0 |
| 21 to 30 | 1.7 |
| 31 to 50 | 1.5 |
| 51 to 70 | 1.4 |
| over 70 | 1.3 |

These are working values for translating from English into longer languages such as German, French, Finnish and Russian, not a standard. A per-key hard limit from `--limits` is an error. A target under 0.3 of a source that is 20 or more characters long is reported as `target_too_short` (possible truncation); that is expected for Chinese, Japanese and Korean, so review it and move on.

## Script contract

`scripts/locale_check.py SOURCE TARGET [--glossary FILE] [--limits FILE] [--no-ratio] [--min-chars N] [--strict]`. Run it; read it only if its output looks wrong. It reads the named files only, writes JSON to stdout and uses no network. `--min-chars` (default 4) is the fewest letters an identical value needs before it counts as untranslated.

Output (one JSON object, ASCII-escaped):

```
{"tool":"locale_check","version":1,
 "source":{"path","format","encoding","keys"},"target":{...},
 "options":{...},"ok":bool,"errors":int,"warnings":int,
 "counts_by_type":{type:int},
 "issues":[{"type","severity":"error"|"warning","key",...details}]}
```

| Issue type | Severity | Meaning |
|---|---|---|
| `missing_key`, `extra_key`, `empty_target` | error | Target lacks a source key, has a key the source lacks, or has an empty value for a non-empty source |
| `placeholder_mismatch` | error | Tokens differ; lists `missing_in_target` and `added_in_target` |
| `icu_missing_other`, `icu_branch_mismatch`, `unbalanced_braces` | error | A plural or select has no `other`; a select lost or gained a branch; braces do not close |
| `tag_mismatch` | error | Markup tags differ |
| `glossary_term_missing`, `do_not_translate_altered` | error | A source term appears but the required translation (or the untouched term) is absent |
| `hard_limit_exceeded` | error | Longer than the key's limit in the limits file |
| `untranslated_identical`, `length_ratio_exceeded`, `target_too_short`, `bidi_control_chars`, `duplicate_key` | warning | Review; `--strict` makes warnings fail |

Exit codes: 0 no error; 1 error (or any issue with `--strict`); 2 unreadable file, bad format or bad glossary, with a message on stderr. Formats: `.json` (nested objects and arrays flattened to `a.b[0]`) and `.properties` (comments, continuations, `\uXXXX`); the two files may use different formats. If Python is not available, do the same checks by hand: key lists, token lists per string, glossary lookups, character counts against the table.

## Report

```
Target: <locale>, <n> keys, register <formal|informal|n/a>
Script: errors <n>, warnings <n> (paste counts_by_type)
Warnings kept on purpose: <key: reason>
Needs context: <keys whose source is ambiguous, with the question>
Glossary: <terms added or decided this run>
Not checked: <e.g. native-speaker review, rendering in the UI, plural rules beyond the listed categories>
```

## Limits

- The script checks surface form. It cannot tell whether a translation is correct or natural, and a native-speaker review is still needed for anything customer-facing.
- Glossary matching is case-insensitive substring matching on the target; heavily inflected languages (Finnish, Russian, Polish) may need several accepted forms listed as an array, or a manual review of reported terms.
- It does not verify that plural categories are the right ones for the language; that is manual step 6.
- Printf positions (`%1$s`) are not compared, only conversion types and counts.
- `length_ratio_exceeded` measures characters, not rendered pixel width. Wide scripts and narrow glyphs differ; test in the UI.
- Not for subtitles with timing, certified translation or legal text; those need a qualified human translator.
