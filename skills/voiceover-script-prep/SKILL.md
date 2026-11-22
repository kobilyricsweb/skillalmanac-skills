---
name: voiceover-script-prep
description: "Prepares a voiceover script for text-to-speech or a narrator (TTS prep): spells out numbers, dates, money, URLs and abbreviations, applies a pronunciation lexicon, chunks under a character limit and estimates duration, with a JSON report of unreadable tokens, long sentences and tongue-twisters. Use when the user says voiceover script, prepare for TTS, text to speech mispronounces numbers, how long will this narration run, or split my script into chunks. Do not use for writing the script, subtitles, voice cloning or audio generation."
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual route in step 3 and the rules in references/spoken-form-rules.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Voiceover script prep

Turn a script written for the eye into one written for the ear, in chunks a speech tool will accept, with a length estimate you can plan around. The script handles English text only and makes no audio.

How this differs from neighbours: a video-script skill decides what the video says and how it is structured; this skill starts after the words are final and only changes how they are written down so a voice reads them correctly.

## Inputs to collect first

1. The script as a UTF-8 file (headings and bullets are fine; each becomes its own paragraph).
2. `--max-chars`: the per-request character limit of the target tool. It is required because limits differ by tool and plan, and none is built in. Ask the user, or have them check the tool's current limit.
3. Speed: `--wpm`, default 155. Use 140 for a calm documentary read, 165 to 170 for upbeat explainer or ad copy. Outside 140 to 170 the report adds an advisory.
4. Names, brands and jargon the voice must say a certain way: write them into a lexicon (step 2).

## Workflow

```
- [ ] 1 Save the script to a file
- [ ] 2 Write the lexicon for names, brands and acronyms
- [ ] 3 Run the script
- [ ] 4 Fix what the report lists, then re-run
- [ ] 5 Deliver files and the fixed summary
```

1. **Save** the script unchanged. Do not paraphrase before the run.
2. **Lexicon** (optional JSON object). A value is either a spoken string or an object with `say` and/or `ipa`:

```json
{"Nguyen": {"say": "win", "ipa": "wɪn"}, "FAQ": "frequently asked questions"}
```

   `say` is written into `spoken.txt`; `ipa` becomes a `<phoneme>` tag in the SSML file. Keys match whole words, case-sensitively, and are applied before every built-in rule. Respelling for a plain-text tool (`say`) is only a workaround; prefer a tool's own pronunciation feature where it has one.
3. **Run**:

```bash
python scripts/prep_voiceover.py script.txt --max-chars 2500 --wpm 155 --lexicon lexicon.json --out-dir out
```

   Run it; do not edit it to make a check pass. Without `--out-dir` nothing is written and only the JSON report is printed. Add `--explicit-breaks` when the target tool honours SSML `<break>` and you want the comma and sentence pauses written into the markup. Without Python: apply the rules in [references/spoken-form-rules.md](references/spoken-form-rules.md) by hand, count words, and estimate seconds as words divided by wpm times 60, plus 0.2 per comma, 0.5 per sentence end and 0.9 per paragraph end (the paragraph pause replaces the sentence pause).
4. **Fix and re-run** until `verdict` is `ready`. Blocking lists, with the usual fix:

| Blocker | Meaning | Fix |
|---|---|---|
| `unexpanded` | a digit string, symbol or all-caps token the rules could not read safely | add a lexicon entry, or rewrite the source text |
| `mixed_script` | letters from a non-Latin script; the rules are English only | give that passage its own voice and language setting, or transliterate it |
| `unmatched_delimiters` | odd number of quotes, or unbalanced brackets, in a paragraph | close or remove the stray mark |
| `chunks_over_limit` | a chunk longer than `--max-chars` (should not occur) | report it as a defect |
| `mid_sentence_breaks` | a single sentence was longer than the limit and had to be cut at a comma, conjunction or space | rewrite that sentence shorter, or accept a break at the clause shown |

   Advisories (do not block): `long_sentences` (over 35 words, adjust with `--max-sentence-words`), `tongue_twisters` (4 or more words in 6 starting with the same sound; sibilants s, sh, z, ch count as one sound), `long_urls`, `mixed_case_tokens` such as brand names, `notes`. Treat a long URL as a script problem: say "link in the description" and cut the address from the spoken text.
5. **Deliver** `spoken.txt`, `chunks.jsonl` and `spoken.ssml`, then this summary:

```
Duration: <est_timecode> at <wpm> wpm (<at_170> to <at_140> seconds across 170 to 140 wpm)
Chunks: <n> of at most <max_chars> characters; <mid-sentence breaks or none>
Changed: <counts from "expansions", e.g. 3 years, 2 currency, 1 URL>
Left for you: <every unexpanded token, long sentence, twister and note, with its line>
Not checked: how any particular voice pronounces the result; non-English passages
```

## Report contract (stdout, strict JSON, `schema_version` 1)

Top-level keys, always present: `schema_version`, `tool`, `input`, `settings`, `verdict` (`ready` or `review`), `blockers` and `advisories` (lists of key names), `totals` (`paragraphs`, `sentences`, `words`, `spoken_chars`, `chunks`, `est_seconds`, `est_timecode`, `est_seconds_at_140_wpm`, `est_seconds_at_170_wpm`), `expansions` (count per rule family), `chunks` (per chunk: `id`, `chars`, `words`, `est_seconds`, `starts_mid_sentence`, `ends_mid_sentence`), `unexpanded`, `mixed_script`, `unmatched_delimiters`, `chunks_over_limit`, `mid_sentence_breaks`, `long_sentences`, `tongue_twisters`, `long_urls`, `mixed_case_tokens`, `notes`. Exit 0 for `ready`, 1 for `review`, 2 for unreadable input or bad arguments (message on stderr).

## What the rules decide, in brief

Years read as pairs (1984 nineteen eighty-four, 2005 two thousand five); a four-digit number counts as a year only after a month name or words such as in, since, by, until, from, and otherwise it is read as a count and listed under `notes`. Dates and times are read in US order; a numeric date such as 03/04/2026 is never guessed and stays under `unexpanded`. `Dr.` and `St.` are read as Doctor and Saint before a capitalised name and as Drive and Street after a capitalised name or number when no name follows; a clash is reported in `notes`. Full tables are in [references/spoken-form-rules.md](references/spoken-form-rules.md); read it when a result surprises you or when working by hand.

## Boundaries

- Disclose a synthetic voice wherever a platform, client or law requires it; offer to add a disclosure line to the script's opening or description.
- Do not prepare a script to imitate a real person's voice, or to put words in a named person's mouth, without that person's permission.
- The skill does not generate audio, clone voices or contact any service.

## Limits

- English only; normalisation follows US conventions (dollars, month-day order, "zero" for 0).
- The duration is an estimate from word counts and fixed pauses. Real voices vary by 10 percent or more; check one rendered chunk against the estimate and rescale with `--wpm`.
- The tongue-twister check looks at first letters only; it misses internal repeats and flags some ordinary alliteration.
- A character limit is measured on the plain spoken text. Tools that count SSML tags toward the limit need a smaller `--max-chars`.
- Sentence splitting treats a single capital letter before a full stop as an initial, so "Plan B. Then" stays one sentence.
- A unit before a noun is read in the plural ("a 6.5 kW system" becomes "kilowatts system"); write "kilowatt" in the source.
- Roman numerals, 3D, MP3 and similar tokens are reported, not guessed.
