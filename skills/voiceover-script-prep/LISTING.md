# Listing page content: voiceover-script-prep

**One line:** Turns a written script into spoken form, chunks it under your tool's limit and estimates its length.

## What it does

The skill walks an agent through preparing an English script for a speech tool or a narrator. A script expands numbers, years, dates, times, money, percentages, units, phone numbers, URLs, e-mail addresses, titles and abbreviations by fixed rules, applies a user lexicon first, splits the text into chunks at sentence boundaries under a limit the user supplies, and estimates duration from words per minute plus pauses (comma 0.2 s, sentence 0.5 s, paragraph 0.9 s). One JSON report lists what the rules could not read safely: leftover digits, symbols and unknown all-caps tokens, mixed scripts, unmatched quotes, sentences over 35 words, tongue-twister clusters and any sentence that had to be cut mid-way.

## Capabilities

- `scripts/prep_voiceover.py`: JSON report; with `--out-dir` also `spoken.txt`, `chunks.jsonl` and `spoken.ssml` (paragraph and sentence tags, spelled-out acronyms, phoneme tags from the lexicon)
- Duration at your wpm plus the range across 140 and 170 wpm
- A decision table for years, dates, `Dr.` and `St.`, acronyms and URLs, usable by hand
- A fixed delivery summary that ends with what was not checked

## When to use

You say voiceover script, TTS prep, my text-to-speech reads numbers wrong, how long will this narration run, or split this script into chunks, and the wording is already final.

## When not to use

Writing the script or planning the video (use a video-script skill), subtitle or transcript repair, translation, generating audio, voice cloning. The skill declines to prepare a script meant to imitate a real person's voice without permission.

How it differs from neighbours: `youtube-content-kit` decides what a video says; `programmatic-video` assembles video from assets. This skill starts after the words are final and only changes how they are written so a voice reads them correctly.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the rules table by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet. What exists is the script on the saved fixtures.

1. `python scripts/prep_voiceover.py evals/fixtures/messy_script.txt --max-chars 400 --lexicon evals/fixtures/lexicon.json --explicit-breaks`: verdict ready, 137 words, 3 chunks, estimate 60.73 s (66.41 s at 140 wpm, 56.05 s at 170 wpm), advisories for one tongue-twister (line 9) and one long URL (line 5). Spoken form of one line: "Join us at three thirty P M on the twenty-second, bring five kilograms of gear, and expect forty-five percent less rain than in the nineteen nineties."
2. The same script without the lexicon: verdict review, exit code 1, `FAQ` listed under `unexpanded`.
3. `python scripts/prep_voiceover.py evals/fixtures/long_sentence.txt --max-chars 120`: verdict review; a 39-word sentence is cut after "the budget," and after "when the vote finally came," and chunks 1 and 2 are listed under `mid_sentence_breaks`.

## Limits

- English only, US conventions (dollars, month-day order).
- The duration is an estimate; real voices vary by 10 percent or more.
- The tongue-twister check uses first letters only.
- The limit is measured on plain spoken text, not on SSML tags.
- A unit before a noun is pluralised ("kilowatts system").
- Roman numerals, 3D, MP3 and similar tokens are reported, not guessed.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 7 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, real TTS output, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a script full of prices, dates and a long link; state the tool's character limit.
2. Run the script: verdict review, `unexpanded` shows `FAQ`; add a lexicon line.
3. Re-run: verdict ready, estimate 1:01, three chunks, and the long URL is flagged for "link in the description".
4. Show `spoken.txt` beside the original, then the summary with "Not checked".

## FAQ seeds

- Does it make the audio? No. It prepares text; any speech tool or person does the voicing.
- Does it need network access? No.
- Which character limit does it use? None built in; you supply `--max-chars` because limits depend on the tool and plan.
- Is the time estimate accurate? It is a model: words over wpm plus fixed pauses. Render one chunk and rescale with `--wpm`.
- Does it work for other languages? No; passages in other scripts are flagged for a separate voice.
- Can I use it to copy someone's voice? No; the skill declines that use.
- How is it different from a video-script skill? Those write the script; this one fixes how finished wording is read.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
