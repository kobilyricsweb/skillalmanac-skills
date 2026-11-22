# Listing page content: translation-and-localization

**One line:** Translates and QA-checks UI strings and docs with protected placeholders, glossary and length checks.

## What it does

The skill gives an agent a seven-step procedure for translating a locale file: classify the strings, fix a glossary and a do-not-translate list, translate into a file with the same keys, run a comparison script, fix every error, do the manual checks the script cannot do, and report in a fixed shape. A table of rules covers named, printf, ICU plural and select tokens, markup tags and apostrophe quoting. A script compares a source and a target locale file (JSON or .properties) and prints strict JSON: missing and extra keys, placeholder and tag mismatches, missing ICU `other` branches, untranslated values, length ratio and per-key limit breaches, glossary and do-not-translate violations. A reference holds the CLDR plural categories per language, right-to-left handling and locale format notes.

## Capabilities

- `scripts/locale_check.py`: one JSON report with `ok`, error and warning counts, counts per issue type and one entry per issue with its key
- Formats: nested JSON (flattened to `a.b[0]`) and Java `.properties`, which may be mixed between source and target
- Glossary file with required terms, accepted alternatives, do-not-translate and allowed-identical lists
- Length ceilings by source length (3.0 for 1 to 10 characters down to 1.3 above 70) plus hard per-key limits
- Exit codes 0, 1 and 2 for scripting in CI
- A reference with plural categories for the main language families, RTL rules and locale formats, with source URLs

## When to use

You ask for a locale file, app copy or a help page to be translated or localized; a vendor translation needs a QA pass; strings broke at runtime because a variable went missing; buttons overflow after translation; terminology differs between files.

## When not to use

Subtitles with timecodes, certified or legal translation, live interpreting, choosing markets, or setting up an i18n library in code. It does not replace review by a native speaker.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent does the same checks by hand (step 6 and the Script contract section).

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill translation run exists yet, so there is no saved translation to show. What exists is the script on the saved fixtures.

1. `python scripts/locale_check.py evals/fixtures/en.json evals/fixtures/fr_bad.json --glossary evals/fixtures/glossary.json --limits evals/fixtures/limits.json` exits 1 with `errors` 11 and `warnings` 2. Issues include: `missing_key extra_src`, `extra_key legacy`, `placeholder_mismatch greeting` (`{name}` missing, `{nom}` added), `placeholder_mismatch msgs` (`%d` became `%s`), `icu_missing_other cart`, `icu_branch_mismatch gender` (the `female` branch is gone), `tag_mismatch terms` (the `<a>` pair is gone), `glossary_term_missing tip` (Dashboard must be Tableau de bord), `do_not_translate_altered signin` (OAuth), `hard_limit_exceeded banner` (85 characters against a limit of 30), `empty_target settings`, and the warnings `length_ratio_exceeded banner` (7.73 against 2.0) and `untranslated_identical btn.submit`.
2. `python scripts/locale_check.py evals/files/t2-qa-spanish/en.properties evals/files/t2-qa-spanish/es.properties` exits 1 with 3 errors: `billing.cancel` missing, `billing.legacy` extra, and `billing.seats` missing `{1}`.
3. The same first command against `fr_good.json` exits 0 with `"ok": true` and an empty issue list.

## Limits

- Surface checks only: the script cannot judge whether a translation is right or natural.
- Glossary matching is a case-insensitive substring test on the target; inflected languages may need a list of accepted forms.
- Plural categories are not verified against the language; that is a manual step.
- Printf argument positions are not compared, only types and counts.
- Length is counted in characters, not rendered width.
- Not for certified, legal or timed subtitle work.

## Distinct from other skills

No other skill in the batch folders (batch_01 to batch_05_sonnet) covers translation, locale files or i18n. Nearest neighbours by topic: `natural-prose-editor` edits English prose and explicitly excludes translation; `document-consistency-check` and `configuration-key-drift-check` compare documents and config keys generally but know nothing about placeholders, ICU or glossaries. Names were checked from folder names only; bodies were not read.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 8 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review, translation quality in any language.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show `en.json` with an ICU plural, a `%d` string and a link tag; ask for German with a glossary.
2. The agent translates, then runs `locale_check.py`; the JSON shows one `placeholder_mismatch` and one `length_ratio_exceeded`.
3. The agent fixes both and re-runs: `"errors": 0`.
4. The report lists warnings kept on purpose, keys needing context and what was not checked.

## FAQ seeds

- Does it need network access? No.
- Does it translate better than a plain prompt? Unmeasured. What it adds is a placeholder rule table, a glossary contract, and a checker that catches broken variables; no comparison run exists yet.
- Does it work with my format? JSON and Java `.properties` are read. XLIFF, PO, ARB and Android XML are not; convert or follow the manual list.
- Will it catch a wrong plural form? No. It checks that an `other` branch exists; the right categories per language are in the reference and in manual step 6.
- What data leaves my machine? None from the script; the agent's own model use is the tool's concern.
- Does it replace a native reviewer? No.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
