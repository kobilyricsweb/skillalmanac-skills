# Expansion and markers

Read this only when the user asks why a ratio was chosen, names a target language, or asks about right-to-left testing.

## Contents

1. Growth by string length
2. Growth by language (planning figures)
3. Pseudo-locale conventions in common platforms
4. Right-to-left wrap
5. Sources

## 1. Growth by string length

Translated text grows more in short strings, because a single short English word often becomes a longer word or a phrase. The script's tiered mode uses the midpoint of the commonly cited ranges:

| English length (characters) | Cited growth range | Tiered value |
|---|---|---|
| up to 10 | 100 to 200 percent | 150 percent |
| 11 to 20 | 80 to 100 percent | 90 percent |
| 21 to 30 | 60 to 80 percent | 70 percent |
| 31 to 50 | 40 to 60 percent | 50 percent |
| 51 to 70 | 31 to 40 percent | 35 percent |
| over 70 | about 30 percent | 30 percent |

These are guidelines, not measurements of any particular product. The flat default (30 percent, 50 percent for 10 characters or fewer) is easier to explain and is the right starting point; use tiered for a layout with many short labels.

How the script applies a ratio: added characters = round(length x ratio). When brackets are on, two of them are the brackets and the rest is `~` padding. A 4-character string at 50 percent therefore becomes exactly 6 characters: `[Šáṽé]`.

## 2. Growth by language (planning figures)

Rough, for choosing `--expansion`; check the real translations when they arrive.

| Target family | Character count versus English | Layout note |
|---|---|---|
| German, Dutch, Finnish, Russian | often 20 to 40 percent longer; long compound words cannot wrap | Narrow columns break first |
| French, Spanish, Italian, Portuguese | about 15 to 30 percent longer | Use the default 0.30 |
| Arabic, Hebrew | similar or slightly shorter | Direction matters more than length (level 4) |
| Chinese, Japanese, Korean | often 30 to 60 percent fewer characters | Glyphs are taller and need more line height, so a limit in characters is the wrong measure |
| Thai, Hindi and other scripts with stacked marks | similar count | Marks above and below the line need vertical room |

## 3. Pseudo-locale conventions in common platforms

Some mobile and browser tooling ships two built-in pseudo-locales: an accented, lengthened Latin one (tag `en-XA`) and a mirrored right-to-left one (`ar-XB`). The script writes `en-XA` into a `.po` header for the first kind; the tag is a convention, any private tag would work. Do not ship the pseudo file as a real locale.

## 4. Right-to-left wrap

Level 4 wraps each string in U+202B (right-to-left embedding) and U+202C (pop directional formatting). These characters are invisible and are not counted in `source_len` or `pseudo_len`. They make a bidirectional-aware renderer lay the English out right to left, so the tester can see punctuation placement, alignment and whether numbers and placeholders keep a sensible order. Real Arabic or Hebrew also needs the interface itself to mirror (navigation order, icons with direction); this check shows only whether the text container follows the direction.

## 5. Sources

Facts above are restated in the author's words from these pages; they were not re-fetched when the skill was written.

- W3C Internationalization, "Text size in translation": https://www.w3.org/International/articles/article-text-size
- Unicode Bidirectional Algorithm, UAX 9: https://unicode.org/reports/tr9/
- Android pseudolocales: https://developer.android.com/guide/topics/resources/pseudolocales
