# Flavour differences

Only Python `re` can be tested by the script. Every other column is knowledge to apply by hand, so results for them are "indicative only". A cell marked "verify (unconfirmed)" was not checked against the engine's current documentation while writing this file; check it before relying on it.

## Contents
1. Construct table
2. Anchor and newline rules
3. Translating a Python pattern
4. Engines without backtracking

Sources (read in the author's own words, not copied): https://docs.python.org/3/library/re.html, https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Regular_expressions, https://www.pcre.org/current/doc/html/pcre2syntax.html, https://github.com/google/re2/wiki/Syntax.

## 1. Construct table

| Construct | Python `re` | JavaScript | PCRE | RE2 / Go |
|---|---|---|---|---|
| Named group | `(?P<n>...)` only | `(?<n>...)` | both forms | `(?P<n>...)`; `(?<n>...)` verify (unconfirmed) |
| Backreference to name | `(?P=n)` | `\k<n>` | `\k<n>`, `(?P=n)` | not supported |
| Lookahead | yes | yes | yes | not supported |
| Lookbehind | fixed width only; alternatives of different length are an error | variable width allowed in current engines (verify (unconfirmed)) | each branch fixed, branches may differ | not supported |
| Atomic group `(?>...)` | Python 3.11 and newer | no | yes | no |
| Possessive `a++` | Python 3.11 and newer | no | yes | no |
| Unicode property `\p{L}` | no | needs the `u` flag | yes | yes (`\pL`, `\p{L}`) |
| `\d` meaning | Unicode digits for str patterns; `re.ASCII` narrows | ASCII `[0-9]` only | ASCII unless UCP is on (verify (unconfirmed)) | ASCII |
| Dot matches newline | `re.DOTALL` / `(?s)` | `s` flag | `(?s)` | `(?s)` |
| Inline flags in the middle | global flags must come first (3.11 and newer reject otherwise); scoped `(?i:...)` is fine | not supported | supported | scoped form supported |
| Recursion `(?R)` | no | no | yes | no |
| `\h`, `\K`, `\R`, `\G` | no | no | yes | no |
| Conditional `(?(1)a\|b)` | yes | no | yes | no |

## 2. Anchor and newline rules

| Anchor | Python | JavaScript | PCRE |
|---|---|---|---|
| Start of text | `^` (without `re.M`), `\A` | `^` (without `m`) | `^`, `\A` |
| End of text | `\Z` is strict; `$` also matches before a final `\n` | `$` is strict without `m` | `\z` strict; `$` also before a final `\n` unless the D option is set |
| `\z` | not before Python 3.14 (verify (unconfirmed)) | no | yes |
| Multiline | `re.M` makes `^` and `$` match at each line | `m` flag | `(?m)` |

Decision: for field validation use fullmatch, or anchors plus the strict end (`\Z` in Python, `\z` in PCRE). With `$` alone, add a no-match case for the value plus `"\n"` and see what happens.

## 3. Translating a Python pattern to another flavour

1. Rename named groups: `(?P<n>` becomes `(?<n>` for JavaScript.
2. Replace `\d` with `[0-9]` if the target is ASCII-only and you want the same result, or the reverse if Unicode digits should match.
3. Replace `\Z` with `\z` (PCRE, RE2) or with `$` without the `m` flag (JavaScript).
4. Remove lookbehind for RE2; restructure with a capture group.
5. Replace `re.fullmatch` semantics by wrapping: `^(?:...)$` with the strict end for the target.
6. Re-run the same case table in the target tool. A case table is the portable part.

## 4. Engines without backtracking

RE2 and Go's `regexp` run in time linear in the input, so the speed risks in `backtracking-risks.md` do not apply to them, but they reject backreferences and lookaround. Rust's `regex` crate follows the same trade-off (verify (unconfirmed)). A pattern that is flagged risky here may be fine there, and a pattern with a backreference cannot move there at all.
