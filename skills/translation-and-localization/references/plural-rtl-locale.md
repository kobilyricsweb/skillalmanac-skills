# Plurals, right-to-left text and locale formats

## Contents
- Plural categories by language
- ICU message patterns
- Right-to-left languages
- Dates, numbers, currency, quotes
- Sources

## Plural categories by language

The categories a plural message needs come from the target language, using the CLDR plural rules. A branch the language never selects is harmless; a missing branch makes the runtime fall back to `other`, which then reads wrongly.

| Language | Categories to write |
|---|---|
| Chinese, Japanese, Korean, Vietnamese, Thai, Indonesian | `other` only |
| English, German, Dutch, Swedish, Italian, Turkish | `one`, `other` |
| Hindi | `one` (0 and 1), `other` |
| French | `one` (0 and values below 2), `many` (large round numbers such as millions), `other` |
| Spanish, Portuguese | `one`, `many` (millions), `other` |
| Russian, Ukrainian | `one` (1, 21, 31 ...), `few` (2-4, 22-24 ...), `many` (0, 5-20 ...), `other` (fractions) |
| Polish | `one`, `few`, `many`, `other` |
| Czech, Slovak | `one`, `few`, `many` (fractions), `other` |
| Arabic | `zero`, `one`, `two`, `few` (3-10), `many` (11-99), `other` |
| Hebrew | `one`, `two`, `other` in current CLDR data (older data also lists `many`; include it only if the runtime still needs it) |

Rules of thumb: write the `other` branch first; write the categories in the table plus any exact `=0` or `=1` branches the source has; do not copy a branch "for completeness" with identical wording unless the language really uses the category. Russian `few` and `many` must carry the right noun form, which is the usual error when the source only has `one` and `other`.

## ICU message patterns

- `{count, plural, one {# file} other {# files}}`: `#` prints the formatted number; keep it, move it freely in the sentence.
- `=0 {...}` matches exactly zero and wins over the category.
- `{gender, select, male {...} female {...} other {...}}`: selector words are keys, never translated.
- `{n, number}`, `{d, date, short}`: the argument and style stay as they are; the formatter localises the output.
- Apostrophe: `'{'` is a literal brace; `''` is a literal apostrophe. A single apostrophe before ordinary text is literal, so French `l'{name}` risks quoting the brace; when in doubt write `l''{name}`.

## Right-to-left languages

Arabic, Hebrew, Persian and Urdu are written right to left.

- Layout mirroring belongs to the UI framework (the `dir="rtl"` attribute or the platform's layout direction), not to the translated string. Do not reorder words to fake it and do not add direction marks to every string.
- A value that mixes translated text with Latin text, digits or a placeholder (a user name, a product code) can display in the wrong order. Wrap the inserted value in a bidi isolate (`<bdi>`, or the Unicode isolate characters U+2068 and U+2069) where it is rendered, not inside the translation.
- Do not mirror: logos, media play and pause icons, clocks, phone numbers, code. Do mirror: back and forward arrows, progress bars, list indentation.
- The script reports U+202A to U+202E (embedding and override controls) that the source does not have; these are almost always accidents and can hide text. Left-to-right and right-to-left marks (U+200E, U+200F) are not reported.
- Digit shapes differ by region and the formatter decides. Do not retype digits into a translation.
- Ask for a screenshot of the translated screen: only the rendered result proves RTL.

## Dates, numbers, currency, quotes

Let the formatter produce these; the translator only chooses the pattern when a string embeds them.

| Item | What varies |
|---|---|
| Decimal and thousands separators | English `1,234.5`; German `1.234,5`; French uses a narrow no-break space as thousands separator and a comma decimal; Swiss German uses an apostrophe |
| Currency | Symbol position and spacing differ (`$5`, `5 $`, `5 EUR`); the symbol is not translated text |
| Dates | Order differs: US month first, most of Europe day first, Japanese and Chinese year first; month and weekday names come from the locale |
| Time | 12-hour in the US and a few others, 24-hour elsewhere |
| Quotation marks | German low-high pair, French guillemets with a non-breaking space inside, Japanese corner brackets, English straight or curly double quotes |
| Punctuation spacing | French puts a non-breaking space before `:`, `;`, `?` and `!`; Spanish opens questions and exclamations with an inverted mark |
| Names and addresses | Order and number of name fields vary; avoid composing a full name from first and last in a translation |
| Units | Imperial against metric is a conversion, not a translation; flag it for the product owner |

Never hard-code a formatted date or number into a string. If the source does, report it under "Needs context".

## Sources

- Unicode CLDR language plural rules: https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html (the category table above summarises it)
- Unicode CLDR plural rules specification: https://cldr.unicode.org/index/cldr-spec/plural-rules
- ICU MessageFormat syntax, including apostrophe quoting: https://unicode-org.github.io/icu/userguide/format_parse/messages/
- Unicode Bidirectional Algorithm (isolates, embeddings): https://www.unicode.org/reports/tr9/
- W3C internationalization, text direction in HTML: https://www.w3.org/International/questions/qa-html-dir
