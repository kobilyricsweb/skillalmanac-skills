---
name: brand-name-shortlist
description: "Names a startup, product, project or channel: use when the user says name my startup, business name ideas, brand name generator, or help me pick between these names. Generates 30 to 60 candidates across five name types, screens them with a script (length, syllables, pronounceability, ambiguous spellings, near-duplicates, competitor collisions, unwanted words, how it reads next to .com) and ends with a shortlist of 5 with reasons. Do not use for logos, brand guidelines, taglines, or for claiming a name is available or trademark-safe."
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the thresholds in step 4 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Brand name shortlist

Turn a naming brief into a shortlist of 5 names that are easy to say, spell and tell apart from competitors, with a to-verify list for what only the user can check. Naming ahead of visual work: a logo or guideline comes after the name survives.

## Hard rule on availability

Never say a name is available, free, clear, safe or unregistered. This skill has no network and no registry access. Domain, handle, app-store and trademark status are always listed as items for the user to check, and for anything beyond a hobby the user should ask a trademark professional. The script scores spelling, sound and collisions with the lists it is given; it does not measure whether a name is good.

## Workflow

```
- [ ] 1 Brief: audience, tone, must-not-imply, languages, where it will be used
- [ ] 2 Generate 30 to 60 candidates across the five types
- [ ] 3 Write the three input files
- [ ] 4 Run the script, read flags, cut
- [ ] 5 Say-it-and-type-it test on the survivors
- [ ] 6 Shortlist of 5 with reasons and the to-verify list
```

1. **Brief.** Ask only for what is missing: who it is for, the feeling (trustworthy, playful, premium), what the name must not imply (a wrong category, a wrong country, a rival), languages and markets where it will be spoken, and the channels (domain, app, handle, spoken aloud in a podcast). Also get 3 to 8 competitor or lookalike names and any words the audience reads badly. Do not invent a brief the user has not given; state your assumptions in one line instead.
2. **Generate.** Aim for 30 to 60, spread over the five types in [references/name-types.md](references/name-types.md): descriptive, invented, compound, metaphor, acronym. At least 6 of each type except acronym (give 0 to 4 unless the user has a long formal name). Vary length. Do not stop at the first 10 and do not generate near-copies of one idea.
3. **Input files.** Save `candidates.txt` (one name per line, optionally `Name | type`), `competitors.txt` and, when relevant, `avoid.txt` (words and fragments that read badly in the audience's languages, including your own entries from the brief). Lines starting `#` are comments.
4. **Screen.** Run the script and read the JSON, not just the shortlist:

```bash
python scripts/score_names.py candidates.txt --competitors competitors.txt --avoid avoid.txt --suffix .com --top 5
```

   Repeat `--suffix` for several (for example `.io`). `--max-per-type 2` (default) keeps the shortlist from being all one type. Run the script; do not edit it to make a name pass. A `cut` verdict is a block (identical to a competitor, contains a word from `avoid.txt`, a long string from the bundled list, no vowels, duplicate) or a score under 50. `review` is 50 to 74 or three or more warnings. Open each cut and review name's flags: a cut can be wrong (a deliberate invented word may trip the consonant heuristic), but you must say why you are overriding it.
5. **Say-it-and-type-it.** For each survivor, apply the two tests in [references/name-types.md](references/name-types.md): could someone type it after hearing it once, and could someone say it after reading it once. The script approximates both; the test decides. Drop any name that fails either test unless the user explicitly wants it.
6. **Shortlist of 5 and report.** Take the script's shortlist as the starting point and edit it with judgement: swap a name only with a reason that you state. Report in this fixed shape:

```
Brief assumptions: <one line>
Candidates: <n generated, n cut by the script, n cut by judgement>
Shortlist:
1. <Name> (<type>): <why it fits the brief>; script score <n>; watch: <flags>
... (5 entries)
To verify yourself before choosing: <domains and handles in slug form, trademark search in the right countries and classes, language check, search results, say-it-and-type-it with three people>
Not checked: availability of every kind; trademark conflict; meaning in languages not supplied
```

   If fewer than 5 names survive, the script exits 1 with `shortlist_shortfall: true`. Generate a second batch in the types that survived best; do not pad the list with weak names.

## Script contract

`scripts/score_names.py` reads the files you name and prints one JSON document. It exits 0 when the shortlist is full, 1 when it is short, 2 on a missing or unreadable file or a bad type. No network, nothing written.

| Key | Content |
|---|---|
| `ranking[]` | `rank`, `name`, `type`, `score` (0 to 100), `verdict` (`keep` 75 and up, `review`, `cut`), `length`, `syllables`, `flags[]` (`code`, `severity` info, warn or block, `detail`), `slugs` (`handle`, `handle_underscore`, `handle_hyphen`, `domains[]`) |
| `shortlist[]` | up to `--top` names, `reasons[]`, `watch[]`, `to_verify[]` |
| `near_duplicate_pairs[]` | names within edit distance 2 (1 when the shorter name has 5 letters or fewer) |
| `shortlist_shortfall` | true when fewer than `--top` survive |
| `not_checked[]`, `notes[]` | what the script cannot know; repeat them in your report |

Flag codes: `length`, `syllables`, `digit`, `hyphen`, `non_ascii`, `multi_word`, `no_vowel`, `consonant_cluster`, `vowel_run`, `q_without_u`, `ambiguous_spelling` (ph/f, gh, ck/k, hard c/k, soft c/s, ough, silent starts, ie/ei), `doubled_letter`, `bundled_offensive`, `avoid_word`, `competitor_exact`, `competitor_substring`, `competitor_near`, `near_duplicate`, `exact_duplicate`, `suffix_join`.

## Thresholds the script applies

| Test | Preferred | Penalised |
|---|---|---|
| Letters | 5 to 10 | 4 letters -5; 3 or fewer -15 to -30; 11 to 12 -8; 13 to 15 -18; 16 or more -30 |
| Syllables | 2 to 3 | 1 syllable -5; 4 -8; 5 or more -20 |
| Consonant run | 2 or fewer | 3 in a row -3 (common) or -8; 4 -15; 5 or more -25 |
| Ambiguous spelling | none | -4 per pattern, capped at -16; doubled letters -3 each, capped at -6 |
| Competitor list | no overlap | contains or is contained (4+ letters) -20; edit distance 2 (1 if short) -25; identical blocks |
| Joined to the suffix | reads cleanly | -6 for a triple letter, consonant pile-up, doubled letter at the dot, or an unwanted string across the dot |

Acronyms skip the sound tests because they are spelled out; they still get length and collision tests.

## Limits

- The syllable and cluster rules are heuristics for English-looking words. Invented words, names from other languages and deliberate respellings can be mis-scored in either direction.
- The bundled unwanted-string list is short and not exhaustive. It misses other languages, slang, spellings with digits or symbols and anything only unfortunate in context; supply `avoid.txt` and ask a native speaker.
- Edit distance finds names that look alike on the page, not names that sound alike.
- Nothing here checks availability or trademark status. A high score is not clearance.
- Score weights are working values, not measured against real naming outcomes.
- Without Python, apply the thresholds table by hand and run both tests in step 5 on every survivor.
