# Listing page content: transcript-cleanup

**One line:** Cleans a raw SRT, VTT or plain transcript into a readable verbatim one, logging every edit, never summarising.

## What it does

The skill gives an agent a fixed procedure: choose a policy (verbatim for legal and research files, clean-verbatim for publication), do a dry run, settle speaker names and terms, run the script, verify, report. The script `clean_transcript.py` parses SRT, WebVTT and plain text (`[hh:mm:ss] Speaker: text` and variants), normalises speaker labels, removes a documented list of fillers and stutters, merges lines that are one broken sentence, rewraps changed cues to two lines of 42 characters, keeps every timestamp, and writes one cleaned file. It prints a strict JSON report with counts, every before-and-after edit, and a token-level check that no word was added.

## Capabilities

- Cleaned `.srt`, `.vtt` or plain `.txt` written to a folder you name; the input is never touched
- JSON report: counts, `speakers.mapping` with the reason for each label change, ambiguous labels, edits with `cue_id`, `words.added`
- Subtitle-limit check on SRT and VTT: lines over 42 characters, more than 2 lines, over 21 characters per second, cues under 1 s or over 7 s, overlaps, gaps under 80 ms
- Optional glossary for speaker names and mis-heard terms
- A `--dry-run` mode that writes nothing

## When to use

You have a machine transcript (Zoom, Whisper, YouTube, Otter-style export, an auto-caption SRT) and want it readable with the same words, the same timing, and consistent speaker names.

## When not to use

Transcribing audio, summarising or minuting a meeting (`meeting-notes-and-actions`), translating, redacting names, rewriting prose to sound better (`natural-prose-editor`), chapter titles. Difference from those: this skill repairs the transcript file itself and measures it; it does not interpret or condense it.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual procedure in `SKILL.md`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixture `evals/fixtures/interview.srt` run with `python scripts/clean_transcript.py evals/fixtures/interview.srt --out-dir out` (exit 1: the report lists subtitle problems).

1. Input cue 1 and 2 (`DR. LEE: Um, so we started the, uh, the trial in 2018,` and `and it ran for, you know, three years.`) become one cue: `Dr. Lee: So we started the trial in 2018,` / `and it ran for three years.`, 00:00:01,000 to 00:00:06,000. The cue that held only "Uh, um." is dropped, and "Uh-huh" is kept because it is an answer.
2. Report excerpt: 7 cues in, 5 out; 6 fillers, 2 stutters, 1 merge, 1 empty cue removed; `DR. LEE` and `Lee` both mapped to `Dr. Lee` (reasons `case` and `title`); words in 50, out 41, added `[]`; after cleaning, cue 3 overlaps the previous cue by 100 ms, cues 2, 3 and 4 are above 21 characters per second (21.3, 22.7, 204.0), cue 4 is under 1 s and has 3 lines. The skill reports these and does not invent new timestamps.

## Limits

- Does not listen to audio or fix recognition errors; a glossary fixes only what you list.
- Filler and stutter rules are English only and are working values.
- Speaker matching uses text only; a unique partial match can still be the wrong person, and the report lists each one to confirm.
- Reading-speed and duration problems are reported, not repaired.
- Chapters and summaries are not produced.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN, and 9 fixture cases pass with hand-checked expected files. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show a Whisper SRT with "DR. LEE", "Lee", "Dr. Lee", ums and split sentences; run `--dry-run` and show the report.
2. Choose `clean-verbatim` (and show `verbatim` for a legal file); run for real.
3. Open the cleaned SRT beside the original: merged cue, one label, timestamps intact.
4. Show `words.added: []` and the list of cues that are too fast to read.

## FAQ seeds

- Will it change what people said? Only by removing the listed fillers and stutters under `clean-verbatim`; `verbatim` keeps them. The script checks that no word is added.
- Does it fix subtitle timing? No. It measures against 42 characters, 2 lines, 21 characters per second, 1 to 7 seconds, and reports the cues.
- Does it need network access? No.
- How is it different from meeting-notes-and-actions? That one turns notes into actions and decisions; this one cleans the transcript and keeps all of it.
- Can it merge two people with the same surname? It refuses and lists the label as ambiguous.
- Does it work for other languages? The filler and stutter rules are English; label handling and formats work for any language that uses a colon after names.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
