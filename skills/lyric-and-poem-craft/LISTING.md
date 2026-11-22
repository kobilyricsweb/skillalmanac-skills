# Listing page content: lyric-and-poem-craft

**One line:** Audits your own lyrics or poem for syllables, rhyme, hooks and clichés, then guides the revision.

## What it does

The skill gives an agent a seven-step procedure: fix the form and brief, save a labelled draft, run an audit script, read the report against stated thresholds, revise one issue type at a time, run an originality check, and report. The script counts syllables per line with a documented vowel-group heuristic (with an override file), detects rhyme scheme from spelling-based end sounds, estimates regularity from syllable counts, finds repeated lines and hooks, matches a bundled stock-phrase list, compares repeated choruses, checks section balance, and verifies seven forms. A hard rule forbids reproducing or closely imitating existing lyrics; the originality step produces a list of phrases to search.

## Capabilities

- `scripts/audit_lyrics.py`: strict JSON with `sections[]`, `rhyme_scheme`, `repeats`, `chorus_consistency`, `section_balance`, `cliches`, `form_check`, `originality`, `flags[]`
- Form checks: verse-chorus, AABA, ballad, sonnet, haiku, limerick, rap bars
- Optional `--compare` against a text you supply, reporting shared word runs of 5 or more
- Reference tables for section lengths, rhyme types and revision moves per flag

## When to use

You are writing your own song or poem and say: fix my chorus, does this rhyme, count the syllables, is my haiku 5-7-5, tighten my bridge, too cliche.

## When not to use

Copying, continuing or imitating an existing song or a named artist's lyrics; rewording a song you love; fetching lyrics; rights clearance; melody and chords. Nearest neighbours: story-structure-planner (prose structure) and natural-prose-editor (prose style); this skill covers meter, rhyme and section analysis for verse.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the same tables by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real runs of the script on the saved fixtures (`evals/fixtures/`):

1. `python scripts/audit_lyrics.py evals/fixtures/song_flawed.txt --form verse-chorus`: verse 1 syllables per line 8, 8, 8, 20 (stdev 5.2, warn); verses of 4 and 7 lines (warn); the second chorus has similarity 0.75 to the first (warn, likely accidental edits); 14 stock-phrase hits in 24 lines (warn); hook "set me free" appears 6 times in the last chorus (info).
2. `python scripts/audit_lyrics.py evals/fixtures/haiku_bad.txt --form haiku`: four lines with 10, 11, 4 and 4 syllables; `form_check.status` is `fail`.
3. `python scripts/audit_lyrics.py evals/fixtures/song_clean.txt --form verse-chorus --title "carry the lantern"`: 20 lines, verse schemes ABAB, chorus AABB, title phrase 2 times in each of 3 choruses, chorus identical, status `pass`, no flags.

## Limits

- English only; syllables and rhyme are spelling-based heuristics that miss some words and over-match some endings.
- Meter is syllable regularity; stress is not analysed.
- Cliché and predictable-rhyme lists are partial; short texts give noisy statistics.
- The script cannot tell whether a line copies published work; the originality step needs a real search, and rights clearance is out of scope.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and 18 script fixture checks pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a verse-chorus draft with a cliché-heavy chorus; run the audit: warnings with line numbers.
2. The agent revises one issue type at a time (line length, then hook, then clichés) and re-runs.
3. Show the originality search list and the recorded search results.
4. Show the final report with the Not checked line.

## FAQ seeds

- Will it write a song in the style of my favourite artist? It will match a genre or mood but refuses to copy or imitate a specific artist's text.
- Can it check that my lyrics are not copied? It lists phrases to search and can compare with a text you supply; it cannot clear rights.
- Is the syllable count exact? No; it is a heuristic with an override file.
- Does it hear rhythm and stress? No, only syllable counts.
- Does it need network access? No.
- Does it work for other languages? No, English only.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet. Accountable editor: Global Media Holdings.
