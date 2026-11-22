# Listing page content: user-research-synthesis

**One line:** Turns many interview notes into themes where every claim cites verbatim quotes by participant id.

## What it does

The skill gives an agent a fixed route from raw interview notes to a report: convert notes to a tagging contract (one idea per note, verbatim text, participant ids, codebook tags), group by affinity in a set order, search for counter-evidence, and write themes to a JSON file. A theme exists only with at least 3 quotes from at least 3 different participants; weaker findings are reported as signals. Confidence levels (low, medium, high) follow participant counts and contradictions, and the report has a fixed structure with a "not checked" section. A script then checks the notes file and the themes file against each other.

## Capabilities

- `scripts/synthesis_check.py`: one strict JSON object with `ok`, a summary, per-theme counts, the highest confidence the evidence allows, and findings with severity, code, location and message
- Errors for: quote not a verbatim excerpt, quote attributed to the wrong participant, unknown note, quote taken from a researcher observation, theme under the evidence threshold, confidence above what the counts allow, "k of T participants" claims that do not match, duplicate ids, tags outside the codebook, missing contradictions field
- Warnings for: untagged notes, one participant dominating a theme or the whole note set, vague quantifiers ("most", "many"), very short quotes, a lowered threshold
- A report contract: question and sample, themes, signals, not covered, check result, not checked

## When to use

You have interview notes or transcripts from several people and want themes, an affinity map or a readout, and the claims must be traceable to what participants said.

## When not to use

Running or scripting interviews (the sibling `jobs-to-be-done-interview` skill covers the interview itself; this one starts after the interviews are done and works across them), survey statistics, summarising a single conversation, clustering thousands of tickets, or building personas from analytics.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual checks in step 8 of the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent-written report. What exists is the script on the saved fixtures.

1. `python scripts/synthesis_check.py evals/fixtures/notes_good.json evals/fixtures/themes_good.json` : `ok` true, 17 notes, 6 participants, 3 themes, 0 errors, 0 warnings. Per theme: T1 3 quotes from P01, P02, P03 with P04 contradicting, highest confidence low; T2 6 quotes from P01 to P06, highest confidence high; T3 3 quotes, highest confidence low. Exit code 0.
2. `python scripts/synthesis_check.py evals/fixtures/notes_good.json evals/fixtures/themes_bad.json` : `ok` false, 12 errors, 2 warnings, exit code 1. Sample findings:
   - `below_threshold` theme TB1: 2 valid quotes from 2 participants; needs at least 3 quotes from 3 participants
   - `count_claim_mismatch` theme TB1: statement says 5 of 6 but the quotes show 2 of 6 participants
   - `quote_not_found` theme TB3: text is not a verbatim excerpt of note N13
   - `quote_participant_mismatch` theme TB3: cites P04 but note N11 belongs to P06
   - `confidence_overstated` theme TB2: declared high but the evidence supports at most low (3 of 6 participants, 0 contradicting)
   - `participant_dominates_theme` (warning) theme TB2: P01 supplies 3 of 5 quotes (60%, limit 50%)

## Limits

- The script proves quotes exist and counts add up; it cannot judge whether a quote supports its theme, whether groups should merge, or whether notes are faithful to the interview.
- Thresholds are working values for small qualitative studies, not statistical tests, and do not make a sample representative.
- Frequency among participants is not importance.
- Text notes only; audio and video need transcribing first.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN, and 8 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste 5 interviews of raw notes; the agent converts them to tagged notes and runs the notes check (untagged notes listed).
2. The agent groups by affinity, searches for counter-evidence and writes themes; the first validation run shows two errors (a quote not verbatim, a count that does not match).
3. The agent fixes both and the second run prints `ok: true`.
4. The report appears: themes with quotes by participant id, one contradiction, a signals section and "not checked".

## FAQ seeds

- Does it need network access? No.
- Why 3 quotes from 3 participants? It is the smallest pattern distinguishable from one person's habit; it is a working default and can be raised.
- Can the agent still write a theme it believes in but that has 2 participants? It goes in the signals section, labelled as something to test.
- How is it different from `jobs-to-be-done-interview`? That skill runs an interview; this one synthesises many finished interviews and checks the evidence.
- Does the script check that the theme is right? No, only that the quotes are real, attributed correctly, and counted correctly.
- Does it work with transcripts in other languages? Quotes are checked as written in the notes; keep the original wording in `text` and mark translations in the report.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
