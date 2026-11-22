# Listing page content: pseudo-localization-tester

**One line:** Builds a pseudo-locale from a resource file and reports truncation, fragment and hard-coded-text risks before translation.

## What it does

The skill gives an agent an eight-step procedure and a script, `pseudo_localize.py`. The script reads a JSON, `.properties` or gettext `.po` file, rewrites every string with accented letters, `~` padding for text growth and `[ ]` brackets (optionally a right-to-left wrap), and writes a sibling pseudo file. Placeholders (`{name}`, `%s`, `%1$d`, `%(x)s`, `${x}`, `{{x}}`), ICU plural and select syntax, HTML tags and entities are protected and compared again after the file is written and re-read. A JSON report lists length-limit risks, sentence fragments, baked-in dates and numbers, unnamed placeholders used twice and, with a source directory, visible UI text that is not in the resource file. It translates nothing.

## Capabilities

- Pseudo-locale file in four levels (accents; plus brackets; plus expansion; plus right-to-left wrap), flat 30 percent growth with 50 percent for short strings, or a tiered table
- Placeholder protection and a round-trip check that fails the run on any difference
- `overflow_risk` with the growth each limited field can absorb (`headroom_pct`)
- Fragment, HTML-in-string, repeated unnamed placeholder and baked date, time, currency or number findings
- Hard-coded text candidates in `.html .htm .jsx .tsx .vue .svelte` files, marked when the text already exists as a resource value
- Refuses to overwrite its inputs; `--dry-run` writes nothing

## When to use

You say pseudo-localization, pseudolocale, i18n smoke test, test text expansion or find hard-coded strings, and want to know what will break before translators see the files.

## When not to use

Translating strings, checking files returned by a vendor (placeholders in translations), choosing fallback locales, or writing a localisation strategy. The nearest neighbour, `translation-and-localization`, covers translating and localising content; this skill creates a test locale and only reports on the source-language file.

## Requirements

Python 3.9 or newer, standard library only, no network. Without Python the agent follows the manual transform in step 8 of the skill and does not produce the report fields.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from `evals/run_fixtures.py` inputs (fixture `evals/fixtures/en.json`, level 3).

1. Prompt: "Make a pseudo-locale for en.json and tell me what needs a developer decision." Command: `python scripts/pseudo_localize.py evals/fixtures/en.json --limits evals/fixtures/limits.json --scan-dir evals/fixtures/src --output en.pseudo.json`. Pseudo strings written:

```
"title":    "[Þĥöţö Šţüðíö~~]"
"greeting": "[Ĥéļļö, {name}!~~]"
"save":     "[Šáṽé]"
"items":    "[{count, plural, one {# íţéɱ} other {# íţéɱš}}~~~~~~~~~~~~]"
"files_deleted": "[Ðéļéţéð %d ƒíļéš ƒŕöɱ %s~~~~~]"
```

   Report excerpt: 10 strings, 9 transformed, 14 placeholders checked, 0 mismatches, round trip ok. `overflow_risk`: `app.greeting` source already over its 10-character limit; `app.save` (limit 5) and `app.title` (limit 14) would overflow with headroom 25 and 16 percent. `fragments`: `app.welcome_prefix` ("Welcome back, ": key name, trailing space, ends with comma) and `app.unread` ("message(s)"). `repeated_unnamed`: `app.files_deleted` (`%d`, `%s`). `baked_values`: a date in `app.last_seen`, the number 3 in `app.unread`. `hardcoded_candidates`: 5 candidates in `Login.jsx`, the last one matching key `app.title`.

2. Prompt: "Make a right-to-left test locale from app.po." Command: `python scripts/pseudo_localize.py evals/fixtures/app.po --level 4`. Plural entry written as `msgstr[0] "[%d ƒíļé šéļéçţéð~~~]"` and `msgstr[1] "[%d ƒíļéš šéļéçţéð~~~]"`, each wrapped in invisible U+202B and U+202C; the header gets `Language: en-XA`; 5 strings, 3 placeholders checked, round trip ok.

## Limits

- Reads the resource file only; text built in code or inside images is not seen. The hard-coded scan is a heuristic over a few template formats.
- Lengths are in characters, not pixels.
- ICU apostrophe quoting and custom placeholder styles are not interpreted.
- Fragment and baked-value findings are guesses from names and patterns.
- Only ASCII letters are accented.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 13 fixture cases pass, including four cases that prove the script refuses to overwrite an input. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real agent run once one exists. Planned beats:

1. A developer points at `en.json` and says the layout breaks in German; the agent picks level 3 and expansion 0.30 and says why.
2. The script runs: gate `ok: true`, 14 placeholders checked, pseudo file written beside the source.
3. The report shows `app.save` with 25 percent headroom and `app.welcome_prefix` as a fragment.
4. The `--scan-dir` pass finds five visible strings in `Login.jsx`, one already in the resource file.
5. The agent hands over the pseudo file with the on-screen test routine.

## FAQ seeds

- Does it translate? No. It only changes English into marked-up English.
- Will it break my placeholders? It protects them and checks again after re-reading the written file; any difference exits 1 and is reported.
- Does it need network access? No.
- Does it change my original file? No; it refuses to write over the source, a limits file or a scanned directory.
- Which formats work? JSON key-value, `.properties` and gettext `.po`/`.pot`. Not XLIFF, ARB, Android XML or iOS strings files.
- How is it different from the translation skill? That one translates and adapts content; this one makes a fake locale to find layout and string-handling bugs before translation.
- Can I ship the pseudo file? No, keep it out of release builds.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). Accountable editor: Global Media Holdings. No human has reviewed it yet.
