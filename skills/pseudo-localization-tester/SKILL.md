---
name: pseudo-localization-tester
description: Use when the user says pseudo-localization, pseudolocale, i18n smoke test, test text expansion, find hard-coded strings, or wants an app checked before files go to translators. Builds a pseudo-locale from a JSON, .properties or gettext .po file with accented letters, growth padding, bracket markers and an optional right-to-left wrap, keeping placeholders and HTML tags intact, and reports overflow risk, sentence fragments, baked-in numbers and dates, and hard-coded UI text missing from the resources. Do not use for translating text, checking translated files or choosing locale fallbacks.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in step 8.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Pseudo-localization tester

Make a fake locale from the source-language file so that localisation bugs show up in the running app before any translator is paid. You are not translating anything. A pseudo string is the same English made hard to miss: accented, longer, bracketed. Placeholders and tags inside it stay byte-identical.

## What each marker exposes

| Marker | Looks like | Bug it exposes |
|---|---|---|
| Accents on every ASCII letter | `Šáṽé` | Plain English still on screen means the text is hard-coded or bypasses the resource file; broken glyphs or `?` mean a font or encoding problem |
| Padding `~` after the text | `Šáṽé~~~` | Truncation, overlapping, clipped buttons, wrapping that breaks the layout |
| Brackets `[` `]` | `[Šáṽé]` | A missing `]` means the string was cut; two bracketed runs touching (`[..][..]`) mean sentences glued together in code |
| Right-to-left wrap U+202B ... U+202C | invisible | Layout that does not mirror, punctuation landing on the wrong side, icons that should flip |

## Choose the level

| `--level` | Adds | Use when |
|---|---|---|
| 1 | accents only | Checking for hard-coded text with no layout change |
| 2 | + brackets | Looking for truncation and concatenation without growth |
| 3 (default) | + expansion padding | Normal pre-translation pass |
| 4 | + right-to-left wrap | The product will ship in Arabic, Hebrew, Persian or Urdu |

Expansion: `--expansion 0.30` is the default growth, and strings of 10 characters or fewer get at least 0.50 because short strings grow more. Use `--expansion 0.50` for a dense UI (toolbars, tables, mobile buttons), `--expansion tiered` for length-based growth (up to 10 chars +150 percent, 20 chars +90, 30 chars +70, 50 chars +50, 70 chars +35, longer +30; rough planning figures), `--no-short-boost` to turn the short-string rule off. Details and per-language growth: read [references/expansion-and-markers.md](references/expansion-and-markers.md) only when the user asks why a ratio was chosen or names a target language.

## Workflow

Copy this checklist:

```
- [ ] 1 Get the source file, format and any length limits
- [ ] 2 Pick the level and expansion
- [ ] 3 Run the script
- [ ] 4 Check ok, round trip and placeholder mismatches
- [ ] 5 Go through the findings
- [ ] 6 Hand over the pseudo file with the test routine
- [ ] 7 Report
- [ ] 8 If Python is missing, do it by hand
```

1. **Inputs.** One resource file: JSON key-value (nested objects and arrays are flattened as `a.b.0`), `.properties`, or `.po`/`.pot`. Optional: `limits.json`, an object mapping a key (for `.po`, the msgid) to the maximum characters the UI allows; and a UI source directory for the hard-coded scan. Ask for limits only if the user knows them; without them the script cannot judge overflow, and the report says so by listing nothing, so tell the user that.
2. **Level and expansion** from the tables above. Say which you chose and why in one line.
3. **Run** (never edit the script to make a check pass):

```bash
python scripts/pseudo_localize.py <source> [--level N] [--expansion X] [--limits limits.json] [--scan-dir <ui-source-dir>] [--output <path>] [--report report.json]
```

   The pseudo file defaults to `<name>.pseudo<ext>` beside the source. The script refuses to write over the source, the limits file, anything under `--scan-dir`, or the report path, even with `--force`; without `--force` it will not replace an existing output. `--dry-run` writes nothing. stdout is one strict JSON report; exit 0 means every placeholder survived, 1 means a mismatch or failed round trip, 2 means a usage or input error and nothing was written.
4. **Gate.** `ok` must be `true`. If `placeholder_mismatches` is not empty or `round_trip_ok` is false, do not hand the file over: show the keys, check [references/finding-classes.md](references/finding-classes.md) for the likely syntax the tokenizer could not read, and report the string as unsupported rather than fixing it by hand.
5. **Findings.** Go through each field of the report in the table below. Each is a question for a developer, never a verdict.
6. **Hand over.** Give the user the pseudo file, the path and the test routine: set the app to the pseudo-locale, open every screen, and look for (a) any readable plain English, (b) a missing `]`, (c) `~` that are cut off or wrap onto a second line, (d) touching brackets, (e) layout that fails to mirror at level 4. The pseudo file is a test artefact: keep it out of release builds.
7. **Report** in the fixed format below.
8. **No Python.** For a handful of strings: map each ASCII letter to an accented one, leave every `{...}`, `%...`, `<...>`, `&...;` and ICU branch keyword untouched, add roughly 30 percent of the length as `~` (50 percent under 11 characters), wrap in `[ ]`, and say the report fields were not computed.

## What each report field means

| Field | Means | Typical action |
|---|---|---|
| `strings_total`, `transformed` | Strings read, and strings that contain letters and were changed | Untransformed strings are listed in `no_letters` (digits, symbols); they cannot show a bug |
| `placeholder_mismatches[]` | A placeholder differs between source and output | Blocks hand-over; see step 4 |
| `overflow_risk[]` | `class` `pseudo_exceeds_limit`: the source fits its limit but a string grown by the chosen ratio does not; `headroom_pct` is the growth the field can absorb. `source_over_limit`: the English alone is already too long | Pick: widen the field, allow wrapping, shorten the source, or accept the risk with the headroom figure written down |
| `fragments[]` | A string that looks like part of a sentence: key name with prefix, suffix, before, after, pre, part, joiner, connector or fragment; leading or trailing space; ends with a comma or `of the a an and or with from`; `word(s)` plural; only placeholders; lowercase start with no final punctuation (`confidence` says how strong) | Ask the developer whether code joins it to other strings; if yes it needs one whole sentence with named placeholders |
| `repeated_unnamed[]` | Two or more `%s`, `%d` or `{}` without position or name in one string | Translators cannot reorder them; switch to `%1$s` or named arguments |
| `html_inside[]` | Markup inside a string | Keep tags paired and out of the translatable words where possible; tag attributes stay untouched |
| `baked_values[]` | A date, time, currency amount or number typed into the text (first kind found per string) | Replace with a formatted placeholder, so the locale decides the format; static counts like "3 steps" need a plural form |
| `hardcoded_candidates[]` | With `--scan-dir`: visible text in `.html .htm .jsx .tsx .vue .svelte` files (text between tags, and `placeholder title alt aria-label label` attributes) that is not wrapped in a resource call. `matches_key` is set when the same text exists in the resource file | A key means "use it here"; null means a resource is missing. Candidates only: text with braces and code are skipped, so absence is not proof |
| `warnings[]` | Unbalanced `{`, malformed ICU branches, duplicate keys, limit keys not found, legacy encoding | Read each one; an unbalanced brace is kept as plain text |

Placeholder families the script protects: `{name}`, `{0}`, `{}`, `{{x}}`, `${x}`, `%s`, `%d`, `%1$s`, `%(name)s`, `%%`, ICU `{n, plural, one {# item} other {# items}}` (selectors and `#` protected, branch words transformed), HTML tags, comments and entities such as `&amp;`.

## Report format

```
Source: <file, format>   Level: <n>   Expansion: <ratio>   Output: <path>
Gate: ok=<true|false>, <n> placeholders checked, <n> mismatches
Overflow: <n> fields, tightest headroom <pct>   (or: no limits supplied)
Fragments: <n> (<high/medium/low counts>)   Baked values: <n>   Repeated unnamed: <n>   Hard-coded: <n or not scanned>
Needs a developer decision: <keys with one-line reasons>
Not checked: <runtime layout, fonts, text built outside the resource file, other formats>
```

## Limits

- Resource file only: the script cannot see text assembled in code, images with text, or strings stored elsewhere. The hard-coded scan is a heuristic over a few template formats.
- Lengths are counted in characters, not pixels or bytes. A limit in pixels needs a visual check.
- ICU apostrophe quoting (`'{'`) is not interpreted, and tag attribute text (`alt`, `title`) inside a string is left as is.
- The `%` rule can mistake a literal percent followed by a letter (`50%c`) for a placeholder; the tool never alters it, so the effect is a skipped word, not a corrupted file.
- Fragment and baked-value findings are guesses from names and patterns; a high fragment count in a clean file is possible.
- Only English-letter transformation is supported; a source in another script gets bracket and padding but no accents.
- JSON output is re-indented with two spaces, `.po` entries are rewritten with one line per field (source order and comments kept), and `.properties` multi-line values are joined onto one line.
