# Finding classes and parser notes

Read this only when a report shows a mismatch, a warning, or the user asks how a finding should be fixed.

## Contents

1. Why a placeholder can mismatch
2. Format notes
3. Fix patterns for findings
4. Sources

## 1. Why a placeholder can mismatch

A mismatch means the placeholder list read from the written output differs from the list read from the source. The script builds output so this should not happen, so a mismatch points at syntax the tokenizer treats differently on the second read:

| Cause | Example | What to do |
|---|---|---|
| Unbalanced `{` (a warning, not a mismatch: it is kept as plain text) | `"Unclosed {name and more"` | Report as a source defect; most message libraries reject it, and the accented text after the brace is not a real test of that string |
| Escaped or quoted braces (ICU apostrophe quoting) | `"It''s '{'literal'}'"` | Unsupported; report the key and test that string by hand |
| A custom placeholder style | `__name__`, `:name`, `$t(key)` | Not recognised, so they may be accented; say which style the project uses and test those strings by hand |
| `%` followed by a letter that is not a conversion | `50%c` read as `%c` | Harmless to the file; the word is skipped |

Never repair a mismatch by editing the pseudo file; fix the source or report the key as unsupported.

## 2. Format notes

| Format | Read | Written |
|---|---|---|
| JSON | Objects and arrays of any depth; only string values are changed, numbers, booleans and null are kept; key names with dots can collide in reports | Two-space indent, non-ASCII kept as is, key order preserved |
| `.properties` | `#` and `!` comments, `=` `:` or whitespace separators, backslash line continuation, `\uXXXX` escapes; UTF-8, with an ISO-8859-1 fallback and a warning | Comments and blank lines kept; values on one line; every non-ASCII character written as a `\uXXXX` escape so Java loaders read it |
| `.po` / `.pot` | `msgctxt`, `msgid`, `msgid_plural`, `msgstr[n]`, multi-line quoted strings, `#` comments | Header kept with `Language` set to the pseudo tag and charset UTF-8; each msgstr filled from the matching English form; plural form 0 from msgid and the rest from msgid_plural, using the `nplurals` value in the header (2 if absent) |

## 3. Fix patterns for findings

| Finding | Pattern |
|---|---|
| Fragment joined in code | One whole-sentence string with named arguments: `"Welcome back, {name}"` instead of a prefix key plus a name |
| `word(s)` or "1 file(s)" | ICU plural `{count, plural, one {# file} other {# files}}` or gettext `msgid_plural` |
| Baked date or amount | A date or number argument, formatted by the locale: `"Last seen {date}"` |
| Repeated unnamed placeholders | `%1$s ... %2$d` or `{user} ... {count}` |
| Overflow with small headroom (under 20 percent) | Allow two lines or truncate with a tooltip; do not shrink font silently |
| `source_over_limit` | The English already exceeds the field: shorten, widen or confirm the limit is right before blaming translation |

## 4. Sources

- ICU message format, plural and select: https://unicode-org.github.io/icu/userguide/format_parse/messages/
- GNU gettext PO file format: https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html
- Java properties file format (Properties.load): https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html
