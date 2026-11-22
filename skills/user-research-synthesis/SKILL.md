---
name: user-research-synthesis
description: Turns many interview notes into evidence-backed themes. Use when the user has interview notes or transcripts and asks for themes, insights, an affinity map, research synthesis or findings from user interviews, or wants a summary that invents nothing. Applies a tagging contract, affinity grouping, a rule of at least 3 quotes from 3 different participants per theme, confidence levels, contradictions and a report citing quotes by participant id; a script checks quotes are verbatim and counts are true. Do not use for running or scripting interviews, survey statistics, or summarising one conversation.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checks in step 8.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# User research synthesis

Turn the notes of several interviews into themes a reader can check. A theme is a claim about several people, so it is supported only by words those people actually said. Your own reading of the notes is a hypothesis until it passes the evidence rule below.

## Evidence rule

A theme is reported as a theme only when it has at least **3 distinct quotes from at least 3 distinct participants** (defaults; `N` and `M` below). Quotes are verbatim excerpts of a tagged note. One person saying a thing five times is one participant. A claim below the rule goes into the report as a **signal**, never as a theme, and is never given a confidence level.

| Level | Needs (all of it) |
|---|---|
| low | N quotes, M participants: the floor for any theme |
| medium | 4+ supporting participants and at least 25% of all participants |
| high | 5+ supporting participants and at least 40% of all participants, and no contradicting participant |

Contradictions lower the ceiling: one contradicting participant stops `high`; contradicting participants numbering at least half the supporting ones force `low`.

- Declare the lowest level you can defend. The script rejects a level above what the counts allow.
- No participant supplies more than half of one theme's quotes (3+ quotes); if one does, add a second voice or say in the report that the theme rests mainly on that person.
- Raise `N`/`M` for big studies if the user asks. Lowering below 3/3 needs the user's say-so and a line in the report; the script floors both at 2.

## Tagging contract

Notes come as JSON, one idea per note (details in [references/formats-and-counting.md](references/formats-and-counting.md)):

```json
{"participants": ["P01"], "codebook": ["tag"],
 "notes": [{"id": "N001", "participant": "P01", "kind": "quote",
            "text": "verbatim words", "tags": ["tag"]}]}
```

1. `text` is what the participant said, copied exactly, no clean-up, no summary. Anything you observed or inferred is `kind: "observation"` and can never be cited as a quote.
2. Participant ids (`P01`), never names; a person keeps one id across all notes.
3. Every note gets at least one tag from the codebook. A tag names a topic (`approval-delay`), not a verdict (`bad`). Add to the codebook only when no tag fits, and say so in the report.
4. A note that fits nothing stays untagged and is listed in the report as out of scope. Do not force a tag.

## Workflow

```
- [ ] 1 Confirm scope: research question, participant count, N and M
- [ ] 2 Convert raw notes to the tagging contract
- [ ] 3 Validate the notes file
- [ ] 4 Group by affinity
- [ ] 5 Search for counter-evidence for every group
- [ ] 6 Write themes.json
- [ ] 7 Validate notes + themes
- [ ] 8 Write the report
```

1. **Scope.** Ask for the research question if absent. Count participants. Fewer than 5: say that high confidence is impossible. Note whether a segment (role, plan, market) matters for splitting.
2. **Convert.** Split raw notes into single-idea notes with ids `N001...`. Copy wording exactly; fix nothing, translate nothing (if the interview language differs from the report language, keep the original in `text` and put your translation in the report, marked as a translation).
3. **Validate notes**: `python scripts/synthesis_check.py notes.json`. Fix errors; tag or list untagged notes; if a participant owns over 30% of notes (4+ participants), mention it in the report.
4. **Affinity grouping**, in this order:
   1. Cluster notes by shared tag. Ignore tags with notes from one participant only; keep them as signals.
   2. Inside a tag, split by the underlying claim ("photo upload fails" and "photo quality is poor" are two groups).
   3. Merge two groups only if one sentence states both without losing a word that matters.
   4. Count distinct participants per group. Groups under N/M become signals.
   5. Name the group last, with the participants' vocabulary and no solution in the title.
   6. Aim for 3 to 9 themes; more means the groups are too fine, fewer means too coarse. This is a guide, not a target.
5. **Counter-evidence.** For every group, read the notes of participants not in it, and the supporting participants' other notes, looking for the opposite or an exception. Put each in `contradictions`. An empty list is valid only after this search; say in the report that you searched.
6. **Write `themes.json`** (schema below). The statement states what was said with counts as "k of T participants" and nothing the quotes do not show. Banned in a statement: most, many, few, several, always, never, often, usually, everyone, nobody; users "want", "need" or "expect" (say what they did or said); causes ("because") the participants did not state. Interpretation goes in a separate `So what` line in the report, labelled as the analyst's reading.
7. **Validate**: `python scripts/synthesis_check.py notes.json themes.json`. Fix every error and re-run; `ok` must be `true`. Read the warnings and either fix or explain each in the report. Run the script, do not edit it to pass.
8. **Report** with the fixed structure below. If Python is unavailable, check by hand: every quote is a substring of its note; each theme has >= N quotes and >= M participants; each "k of T" matches a count you did; no participant over half a theme; confidence not above the table.

## themes.json

```json
{"thresholds": {"min_quotes": 3, "min_participants": 3, "max_share": 0.5},
 "themes": [{"id": "T1", "title": "...", "statement": "3 of 6 participants said ...",
             "confidence": "low|medium|high",
             "quotes": [{"participant": "P01", "note": "N001", "text": "verbatim excerpt"}],
             "contradictions": []}]}
```

A quote may use `...` for a cut; the pieces must still appear in order in the note. Brackets with added words are not allowed.

## Report contract

Use these headings, in this order:

1. **Question and sample**: the research question; `T` participants (segments if any); N and M used; what was excluded and why.
2. **Themes**: for each, in order of participants supporting: id and title; `Confidence: low|medium|high` with the counts that justify it; statement; the quotes as `P03 (N06): "excerpt"` one per line; `Against:` the contradicting quotes in the same form, or "searched, none found"; `So what:` one labelled analyst reading, optional.
3. **Signals (below the evidence rule)**: single or two-person observations, each with participant id and note id, no confidence level, framed as "to test".
4. **Not covered**: untagged notes, participants not cited by any theme, tags added to the codebook.
5. **Check result**: the script's `summary` figures (errors, warnings) and the warnings you accepted, each with the reason.
6. **Not checked**: that notes capture the interviews faithfully; whether the sample represents the user base; meaning of quotes beyond the words.

Never write "users" for a result about T participants; write "participants".

## Script

`scripts/synthesis_check.py NOTES.json [THEMES.json] [--min-quotes N] [--min-participants M] [--max-share F] [--strict]`: run it. Prints one strict JSON object: `ok`, `summary`, per-theme counts and `max_confidence`, and `findings` (`severity`, `code`, `where`, `message`). Errors: quote not verbatim, wrong participant, unknown note, quote from an observation, theme under N/M, confidence overstated, wrong "k of T" claim, duplicate ids, unknown tag, missing contradictions field. Warnings: untagged note, participant over-represented (in a theme or in all notes), vague quantifier, short quote, lowered threshold. Exit 0 ok, 1 errors (or warnings with `--strict`), 2 unreadable or invalid input.

## Limits

- The script proves the quotes exist and the counts add up. It cannot tell whether a quote supports its theme, whether two groups should merge, or whether the notes are faithful to the interview.
- Thresholds (3 quotes, 3 participants, 50% share, 25% and 40% participant shares) are working values for small qualitative studies, not statistical tests; they do not make a sample representative.
- Frequency among participants is not importance. A theme backed by 3 people can matter more than one backed by 6; the report should say what is known, not rank by count alone.
- Works on text notes. Audio, video and screenshots must be transcribed or described first.
- Tags and groups are the analyst's judgement; a second reviewer coding a sample would give a better check than any script.
