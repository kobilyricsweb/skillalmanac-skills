# Formulas, heuristics and limits

Read this when the user asks how a score is computed, disputes a number, or gives text that is not ordinary English prose (forms, tables, poetry, dialogue, text full of numbers).

## Contents

- Formulas and constants
- Reading-ease bands
- How the script counts
- What the scores cannot tell you
- Sources

## Formulas and constants

With W words, S sentences and Y syllables:

| Measure | Formula | Notes |
|---|---|---|
| Flesch reading ease | 206.835 - 1.015 x (W / S) - 84.6 x (Y / W) | Higher is easier. Can go above 100 or below 0 on extreme text. |
| Flesch-Kincaid grade | 0.39 x (W / S) + 11.8 x (Y / W) - 15.59 | An estimate of US school years. Can be negative for very simple text. |
| Average sentence length | W / S | Reported in words. |

Both use only two inputs: how long the sentences are and how long the words are. Neither sees vocabulary difficulty, order of ideas, layout, or what the reader already knows.

Worked check (also the first fixture): "The office will close early on Friday. Please bring your form to the front desk." has 15 words, 2 sentences, 18 syllables. Ease = 206.835 - 1.015 x 7.5 - 84.6 x 1.2 = 97.7. Grade = 0.39 x 7.5 + 11.8 x 1.2 - 15.59 = 1.5.

## Reading-ease bands

| Ease | Label | Usual US school-grade reading |
|---|---|---|
| 90 to 100 | very easy | about grade 5 |
| 80 to 90 | easy | about grade 6 |
| 70 to 80 | fairly easy | about grade 7 |
| 60 to 70 | plain English | about grade 8-9 |
| 50 to 60 | fairly difficult | about grade 10-12 |
| 30 to 50 | difficult | college |
| 0 to 30 | very difficult | college graduate |

The labels are a convention attached to the formula, not a finding about your readers.

## How the script counts

- **Words**: runs of letters (with inner apostrophes and hyphens) and numerals. A numeral counts as one word of one syllable, although it is spoken with more syllables; text full of numbers therefore scores easier than it reads aloud.
- **Sentences**: paragraphs are split after . ! or ? followed by a capital letter or digit. Titles and a few abbreviations (Mr., Dr., St., vs., e.g., i.e., No., U.S.) do not end a sentence. Hard-wrapped lines are joined into one paragraph. A line without end punctuation that is not marked as a Markdown heading is joined to the next line of its paragraph, so mark headings with # or leave a blank line after them.
- **Excluded from sentence counts**: Markdown headings, list items, table rows, fenced code, inline code, URLs and e-mail addresses. The report counts them under `input.excluded`. They are still searched for numbers, links, names and the jargon list. Consequence: a document made mostly of lists is scored on its few prose sentences only.
- **Syllables**: vowel groups (a e i o u y), minus a silent final e, minus a silent -es or -ed ending, minimum one per word, plus a short override table for words the rule gets wrong. It is a heuristic. A fixture checks 67 hand-counted words, but the overrides were added after the first run, so that is not an independent accuracy figure. Expect occasional one-syllable errors on names, compounds and foreign words.
- **Passive candidates**: a form of be (am, is, are, was, were, be, been, being, and the n't forms), optionally with adverbs between, followed by a past participle (a word ending in -ed of five or more letters, or a word from a built-in list of irregular participles). Adjective-like words (tired, interested, entitled and similar) and "used to" are skipped. It misses passives with other verbs ("gets denied") and flags some adjectives ("is limited"). Each hit says whether a "by" agent follows in the sentence (`agentless`).
- **Uncommon words**: words that are not in a built-in list of about 880 everyday English words, after stripping common endings (-s, -es, -ed, -ing, -ly, -er, -est). Names (capitalised mid-sentence), all-capital acronyms and words of three letters or fewer are not counted. The list is hand-made, not a frequency corpus, so "uncommon" means "not on this list". `rare_word_share` is uncommon words divided by countable words.
- **Complex words**: words of three or more syllables, as a share of countable words.
- **Numbers**: every numeral outside code and URLs, with currency signs, percent signs and thousands commas removed (`$1,250.50` becomes `1250.50`; `7:40` stays as written). Compared as sets, so a number repeated twice and kept once is not reported. The digits 0 to 20 written as words in the rewrite are reported separately as `spelled_out_in_rewrite`, not as missing.
- **Modals, negations, conditions**: counts of must, shall, should, may, might, can, cannot, can't, could, will, won't; of not, no, never, none, nobody, nothing, neither, nor, cannot, without and n't forms; and of if, unless, except, only, until. A change is a warning to confirm by reading, never an automatic error, because "shall" to "must" is a legitimate edit and "may" to "must" is not.

## What the scores cannot tell you

- Whether a reader understands the text. A short sentence full of unfamiliar ideas scores easy; a long, well-built sentence on a familiar topic scores hard.
- Whether the rewrite is accurate. Meaning checks are by reading, in the workflow's step 7.
- Anything about languages other than English. The script refuses text it detects as non-English (fewer than 15 percent common English function words, or mostly non-Latin letters) and gives no score.
- Short samples. Under 100 words or 5 sentences the report is flagged low-reliability; one sentence can move the grade by several points.
- Gaming. Chopping every sentence in half lowers the grade and can make the text harder to follow, because the links between ideas disappear. The script warns when the average falls under 8 words.
- Style: tone, warmth, cultural fit, accessibility needs beyond reading level (layout, contrast, screen-reader order).

## Sources

Read in your own words and not copied:

- Flesch's 1948 article "A new readability yardstick" gives the reading-ease formula; the grade formula comes from Kincaid and colleagues' 1975 US Navy report on readability for enlisted training material. Overview with both formulas: https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests
- US federal plain-language guidelines (sentence length, active voice, address the reader, lists, definitions): https://www.plainlanguage.gov/guidelines/
- ISO 24495-1:2023, plain language, governing principles and guidelines (catalogue entry): https://www.iso.org/standard/78907.html
