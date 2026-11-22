---
name: transcript-cleanup
description: Cleans a raw transcript or subtitle file (SRT, WebVTT, timestamped text) into a readable verbatim transcript, never summarising. Use when the user says clean up this transcript, remove the ums, fix the speaker names, tidy this auto-caption or SRT, or a Zoom, Whisper or YouTube transcript is messy. A script removes listed fillers and stutters, merges broken lines, normalises speaker labels, keeps timestamps, logs every edit, writes the cleaned file and reports subtitle-limit problems as strict JSON. Do not use for transcribing audio, summarising, meeting minutes, translation, redaction or polishing prose.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in the last section of this file.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Transcript cleanup

Turn a raw speech-to-text file into a clean transcript that says exactly what was said. The words belong to the speaker: this skill repairs form (fillers, line breaks, labels), never content. It does not summarise, paraphrase, correct grammar, or fill gaps.

## Policy: decide before touching the file

| Situation | Policy | Fillers and stutters |
|---|---|---|
| Legal, research coding, compliance, interview evidence, anything quoted as "what they said" | `verbatim` | Kept. Only labels and line structure are normalised |
| Publication, captions, show notes, readable archive | `clean-verbatim` (default) | Listed fillers and stutters removed |
| The user wants shorter or smoother wording | Out of scope | Hand off to `natural-prose-editor` |

If the user does not say which, use `clean-verbatim` and say so in the report. If the file looks like testimony or a research interview, ask once.

Removed under `clean-verbatim`, and nothing else:

| Rule | Removed | Never removed |
|---|---|---|
| Filler sounds | um, umm, uhm, uh, er, erm, hm, hmm, mm (any stretch of the letters) | uh-huh, mm-hmm, hm-mm (they answer yes or no); all-caps tokens of 3 letters or fewer such as ER, UM, UH |
| Filler phrases | "you know," and "I mean," only when set off by commas or opening a sentence | "as you know", "do you know", "like", "so", "right", "sort of", "kind of" |
| Stutters | an immediately repeated word from this list: I, we, you, he, she, they, it, the, a, an, and, but, to, of, in, is, was, my, and the contractions I'm, it's, that's, we're, they're, you're; also hyphen forms such as "I-I" | Repeats of "that", "had", "no", "very", "so": they can be real |

Removing a filler keeps a comma only after yes, no, well, so, okay, right, sure, yeah, now, anyway, actually, basically, and, but ("Well, um, I think" becomes "Well, I think"). A capitalised filler at the start of a cue capitalises the next word; a lowercase one does not.

## Workflow

```
- [ ] 1 Identify input and policy
- [ ] 2 Dry run and read the report
- [ ] 3 Settle speakers and terms
- [ ] 4 Run for real
- [ ] 5 Verify the report
- [ ] 6 Report to the user
```

1. **Identify.** The script detects SRT, WebVTT, or plain text on its own (`--format` overrides). Plain lines may look like `[hh:mm:ss] Speaker: text`, `hh:mm:ss text`, `Speaker: text`, a timestamp alone on a line, or bare text. A leading `mm:ss` or `hh:mm:ss` is always read as a timestamp. Keep the original file untouched.
2. **Dry run.** `python scripts/clean_transcript.py INPUT --dry-run --policy <policy>` prints the report and writes nothing. Look at `speakers`, `counts`, and `checks`.
3. **Speakers and terms.**
   - `speakers.mapping` lists every label that was changed and why: `case`, `title` ("Dr. Lee" and "Lee"), `generic-number` ("SPEAKER_01" and "spk1" become "Speaker 1"), `partial-name` ("Sarah" into "Sarah Lee"), `glossary`.
   - A `partial-name` merge is a guess made from text alone: check it against the file before accepting it.
   - `speakers.ambiguous` means a short label fits two or more full names (for example "Lee" with "Sarah Lee" and "Tom Lee"). Nothing was merged. Ask the user who it is, then put the answer in a glossary.
   - Glossary file: `{"speakers": {"alias": "Full Name"}, "terms": {"wrong": "Right"}}`. Use only spellings the user gave or that appear in the source material; never invent a name. Terms match whole words, case-insensitively, longest first.
4. **Run.** `python scripts/clean_transcript.py INPUT --out-dir DIR --policy <policy> [--glossary FILE]`. It writes one file, `<stem>.cleaned.<ext>`, never the input. Plain output keeps each original timestamp string; SRT is renumbered from 1; VTT keeps cue identifiers and settings and drops NOTE, STYLE and REGION blocks (the report warns).
5. **Verify.** Exit 0 means nothing is left to review; exit 1 means the report lists something; exit 2 is a usage or input error. Check:
   - `words.added` is `[]`. A word there is a defect: do not deliver, and do not edit the script.
   - `counts.segments_removed_empty` cues were only fillers; their timing gap now exists.
   - Sample the `edits` list (each has `cue_id`, `rule`, `before`, `after`; it is capped at 1000 and `edits_truncated` says so).
6. **Report** in the fixed shape below.

## What the script merges and rewraps

Two neighbouring segments become one only when all hold: the first has no sentence-final punctuation (`. ? ! …` or a trailing `--` or dash), the second starts lowercase or the first ends with `, ; :`, the speaker is the same (or the second has none), no blank line separates them, and for cues the silence between them is at most 1.0 s (`--merge-gap`), the merged cue lasts at most 7 s and holds at most 84 characters. Plain timestamped lines further than 15 s apart are not merged. `--no-merge` turns merging off. Cues that were not changed keep their original line breaks; changed cues are rewrapped to at most 42 characters per line, split after punctuation when both halves fit. A cue with two or more lines starting with a dash is multi-speaker dialogue and is left untouched.

## Subtitle limits the script measures (SRT and VTT only)

| Check | Flagged when |
|---|---|
| `line_length` | a line is over 42 characters (voice tags not counted) |
| `too_many_lines` | more than 2 lines |
| `reading_speed` | more than 21 characters per second (visible characters, line breaks excluded) |
| `too_short` / `too_long` | under 1.0 s or over 7.0 s |
| `overlap` | a cue starts before the previous one ends |
| `short_gap` | under 80 ms between cues |
| `bad_timing`, `empty` | end not after start; no visible text |

`checks.before_counts` is the input, `checks.after` the output with `cue_id` evidence (the cue number in the cleaned file; the `edits` list uses source ids). The script only measures. Fixing reading speed or duration means changing timing or cutting words: under `verbatim` cutting is forbidden, under `clean-verbatim` it is the user's decision. List the flagged cues and offer options; do not guess new timestamps.

## Report format

```
Policy: <verbatim | clean-verbatim> and why
Changed: <n fillers, n stutters, n merges, n cues dropped, n labels, n glossary terms>
Speakers: <final list; partial-name merges to confirm; ambiguous labels>
Subtitle limits: <categories with counts and cue ids, or "not applicable (plain text)">
Integrity: words.added = [] ; words in <n> out <n>
Not checked: <accuracy against audio; spelling of names not in the glossary; anything the script cannot see>
Output: <file path>
```

Give the path to the cleaned file, not the whole text, unless the user asked for it in chat.

## Limits

- The script does not listen to audio, correct recognition errors, add punctuation, or fix grammar. A wrong word stays wrong unless a glossary term covers it.
- Filler and stutter rules are English only and are working values, not measured optima. A real "er" or "um" in a quoted name is kept only when written in capitals of 3 letters or fewer.
- Speaker matching is text-only. Two people sharing a surname or first name look identical; ambiguous cases are reported, but a unique partial match can still be wrong.
- Label detection needs a capitalised name of up to four words followed by a colon (or word plus number such as "guest 1"). Words like Note, Warning, Time are not treated as speakers.
- Cue ids in the cleaned SRT are renumbered. Styling tags other than a leading VTT voice tag are left in the text.
- Chapters, titles and summaries are not produced: a chapter title is a summary. Silence gaps of about 4 seconds or more between cues are visible in the timestamps if the user wants to place chapter breaks themselves.
- Files are read as UTF-8, UTF-16 with BOM, or cp1252 (with a warning) and written as UTF-8.

## Manual procedure without Python

Work in this order and keep a before-and-after note for every change: (1) copy the file; (2) keep timestamps exactly; (3) delete only the fillers in the table above, and only under `clean-verbatim`; (4) join a line to the next only when the first has no sentence-final punctuation and the next starts lowercase; (5) pick one spelling per speaker and use it everywhere; (6) count words before and after and explain every difference; (7) for subtitles, count characters per line and per second against the limit table and report, do not repair.

## Files

- `scripts/clean_transcript.py`: run it, do not edit it to make a check pass. Usage is in its docstring.
- [references/format-and-limits.md](references/format-and-limits.md): read when a file has unusual timing syntax, when the user asks why a limit is 42 or 21, or when choosing between subtitle conventions.
- [references/edge-cases.md](references/edge-cases.md): read when the report shows a surprise (labels mistaken for speakers, merges you disagree with, lost cues).
