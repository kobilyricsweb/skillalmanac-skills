---
name: plain-language-readability
description: Rewrites public-information, government, customer-support and teaching text into plain language at a stated reading level, with a script that measures Flesch reading ease, Flesch-Kincaid grade, sentence length, passive voice, uncommon words and the user's own jargon list, then checks that numbers, links and obligation words survived. Use when the user says plain language, plain English, simplify this notice, lower the reading level, make it grade 6, easier to read, or asks for a readability score. Do not use for removing AI tone (natural-prose-editor), translation, summarising, legal or medical sign-off, or getting past AI-detector or plagiarism checks.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual fallback below.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Plain-language readability

Rewrite English text so the intended readers can use it, and prove with numbers what changed. Wording and structure change; meaning never does. A score is a smoke alarm, not a verdict: no grade level guarantees that anyone understands the text.

## Preserve-facts rule

Never change, add or drop: numbers, amounts, dates, deadlines, times, names, form and law references, links, e-mail addresses, phone numbers, conditions (if, unless, except, only, until), negations, or the strength of an obligation (must, should, may, will). If a sentence cannot be simplified without risking one of these, leave it and list it for the author. Do not add facts, examples or reassurance. Where the source is vague or ambiguous ("may not"), keep it vague and flag it.

## Decision tables

Reading-ease bands (Flesch, English only): 90+ very easy (about grade 5); 80-90 easy (6); 70-80 fairly easy (7); 60-70 plain English (8-9); 50-60 fairly difficult (10-12); 30-50 difficult (college); under 30 very difficult.

Starting targets when the user gives none. These are working values from common plain-language practice, not legal standards. The user's number wins, and so does any regulation or contract that sets its own level. State the target you used.

| Audience and purpose | Flesch-Kincaid grade | Average sentence | Sentences over 25 words | Passive sentences |
|---|---|---|---|---|
| General public notice or letter | 8 or lower | 17 words or fewer | 0 | 15% or fewer |
| Benefits, health or safety instructions | 6 or lower | 15 or fewer | 0 | 10% or fewer |
| Customer-support reply or macro | 8 or lower | 17 or fewer | 0 | 15% or fewer |
| Lesson text for grade g | g, give or take 1 | 10-14 for grades 3-5, 12-16 for 6-8 | 0 | 15% or fewer |
| Internal staff guidance | 10 or lower | 20 or fewer | 1 per page at most | 20% or fewer |

Rewrite moves per finding (details and checks in [references/rewrite_moves.md](references/rewrite_moves.md); read the section for the finding you are fixing):

| Finding | Move |
|---|---|
| Sentence over 25 words | Split at the join between ideas; keep each condition with its instruction |
| Passive without an actor | Name the actor only if the source says who; otherwise keep and flag |
| Uncommon word with a plain swap | Swap if the meaning is identical; never swap a keep-list term |
| Wordy phrase | Use the short form (in order to / to) |
| Action or deadline at the end | Move it to the front |
| Needed technical term | Keep it, define it once in 15 words or fewer at first use |
| "Shall", "may" | See the modal table in the reference; "may" to "must" is a change of meaning |

Stop rule. Stop when all of these hold: the target is met or the user says it is enough; `numbers_preserved` is true and no link changed; each modal, negation and condition warning has been read and confirmed; every keep-list term is present with a gloss; no choppy-text warning. Hard stops: three rewrite rounds; a rewrite under 60% of the original length (restore what was cut); a grade still above target only because of keep-list terms (report it, do not strip the terms).

## Workflow

```
- [ ] 1 Collect audience, target, purpose, jargon list
- [ ] 2 Save the original; write the rewrite to a new file
- [ ] 3 Measure the original
- [ ] 4 Plan the moves from the findings
- [ ] 5 Rewrite, smallest change first
- [ ] 6 Compare, fix, repeat (3 rounds at most)
- [ ] 7 Read both versions side by side
- [ ] 8 Report
```

1. **Collect.** Audience and purpose, target grade (else the table above), words that must stay (names, forms, legal terms) and words to replace. Ask only for what is missing and cannot be defaulted. Write the jargon list, one term per line: `term` (replace), `term => plain` (replace with this), `!term` (needed, keep and gloss). Lines starting with `#` are comments.
2. **Save.** If the text exists only in chat, save it to `original.md`. Never edit the original. The script reads files only.
3. **Measure.** `python scripts/readability.py original.md --grade 8 --jargon jargon.txt` (omit options you do not have). Read `scores`, `long_sentences`, `passive`, `rare_words`, `wordy_phrases` and `jargon`. A `low_reliability` flag means under 100 words or 5 sentences: treat the numbers as rough and rely on the findings.
4. **Plan.** List the moves per finding and the terms that stay. Quick win order: structure, vocabulary, passive, gloss.
5. **Rewrite.** Change one kind of thing at a time. Keep headings, lists and table layout unless a finding says otherwise.
6. **Compare.** `python scripts/readability.py original.md --rewrite rewrite.md --grade 8 --jargon jargon.txt`. Exit 1 means something in `failures` must be fixed: numbers or links changed, a keep-list term dropped, or the target missed. `comparison.warnings` are not failures; each one needs a read and a decision.
7. **Read side by side**, sentence by sentence: who must do what, by when, under which condition, with which exception, for how much. The script cannot see a claim reworded into a different claim.
8. **Report** in the fixed shape below. Give the rewritten text first.

## Script contract

`scripts/readability.py` (run it; do not edit it to make a check pass):

```
python scripts/readability.py TEXT [--rewrite FILE] [--grade N] [--max-sentence-words N]
                                   [--jargon FILE] [--out FILE [--force]]
```

Prints one strict JSON object. With `--rewrite`, `scores`, `long_sentences`, `passive` and `rare_words` describe the rewrite and `comparison` holds before and after. `--out` also saves the JSON; it refuses any path that is the text, rewrite or jargon file (even with `--force`) and refuses an existing file without `--force`.

| Key | Content |
|---|---|
| `scored` | `text` or `rewrite` |
| `input` | `words`, `sentences`, `syllables`, `excluded` (headings, list items, table rows, code), `low_reliability`, `reliability_notes[]` |
| `scores` | `flesch_reading_ease`, `ease_band`, `fk_grade`, `avg_sentence_words`, `long_sentence_count`, `passive_count`, `passive_share` (share of sentences), `rare_word_share`, `complex_word_share` |
| `target` | `fk_grade_max`, `measured`, `met`, or null |
| `long_sentences[]`, `passive[]`, `rare_words[]`, `wordy_phrases[]`, `jargon[]` | findings with sentence numbers, matched text, plain suggestions, per-term status (`remaining`, `replaced_or_absent`, `kept_with_gloss`, `kept_no_gloss`, `dropped`) |
| `comparison` | null, or `metrics` (before, after, delta, improved), `numbers` (missing, added, spelled_out_in_rewrite), `links`, `modals`, `negations`, `warnings[]` |
| `numbers_preserved` | true, false, or null when there is no rewrite |
| `failures[]`, `ok` | what made the exit code 1 |

Exit codes: 0 passed; 1 a check failed; 2 bad input (missing or empty file, non-English text, no prose sentences, refused `--out`). The script refuses to score non-English text. Formulas, heuristics and their limits: [references/formulas_and_limits.md](references/formulas_and_limits.md); read it when the user disputes a score or the text is not ordinary prose.

Manual fallback without Python: take a 100-word sample, count words W, sentences S and syllables Y by hand; ease = 206.835 - 1.015 W/S - 84.6 Y/W; grade = 0.39 W/S + 11.8 Y/W - 15.59. Underline sentences over 25 words, passives (be + past participle), and any word not in everyday use; compare every number, date and link in both versions by eye. Say in the report that the figures are hand counts.

## Report

```
Target: <audience, grade, purpose; whether the target was given or defaulted>
Before -> after: grade 11.1 -> 4.0; ease 52.0 -> 87.4; average sentence 20.6 -> 11.9 words; sentences over 25 words 3 -> 0; passive sentences 57% -> 10%; uncommon words 16% -> 6%
Facts: numbers preserved yes/no (list any difference); links yes/no; modal, negation and condition warnings and how each was confirmed
Kept on purpose: <needed terms with the gloss used; sentences left alone and why>
Left for the author: <ambiguous words, unknown actors, claims that look inconsistent>
Not checked: comprehension by real readers; legal, medical or technical accuracy; anything outside the text
```

## Boundaries

- Do not present a score as proof that readers understand, as legal compliance, or as accessibility certification.
- Do not use the tools to make machine-written or paraphrased text pass an AI detector or plagiarism check, or to disguise authorship where disclosure is required. Decline that goal; plain-language editing is still on offer.
- Text that decides someone's rights, money or health (notices, consent forms, dosing) needs sign-off by the accountable person; say so in "Left for the author".

## Limits

- English only; formulas count surface length and syllables, not difficulty of ideas. A short sentence on an unfamiliar topic scores easy.
- Syllable counts are a heuristic; numerals count as one syllable. The common-word list is small and hand-made. The passive check misses some passives and flags some adjectives.
- Under 100 words the figures are unstable. Lists and headings are left out of sentence statistics.
- Numbers are compared as sets of values; units, currency and percent signs are only warned about. Names, modals and conditions are warnings, not proofs.
- The starting targets are working values, not standards, and have not been tested with real readers.
