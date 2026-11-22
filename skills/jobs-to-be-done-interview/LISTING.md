# Listing page content: jobs-to-be-done-interview

**One line:** Plans, scripts and analyses switch interviews, and checks transcripts and job statements for leading questions and gaps.

## What it does

The skill gives an agent three modes: prepare (switch definition, recruiting screen, a 55-minute timeline guide), script (non-leading question rules with rewrites, for the agent as co-pilot) and analyse (code push, pull, anxiety and habit with verbatim quotes, then write "When ..., I want to ..., so I can ..." statements backed by two or more interviews). A script reads one study JSON file and reports leading questions by pattern, forces coverage per interview, quotes that are not in their turn, and job statements missing a situation, motivation or outcome. Output is a single JSON object with an exit code.

## Capabilities

- `scripts/jtbd_check.py`: strict JSON report, exit 0 ok, 1 errors, 2 input problem
- Interview guide: timeline with minutes per phase, probes per force, rewrites of bad questions
- Study file template and a coding contract (quotes must be verbatim, `none_found` needs a note)
- Fixed analysis report that lists what was not checked

## When to use

You are a founder or PM who says JTBD interview, switch interview, why did customers switch, code my transcripts, forces diagram, or write job statements.

## When not to use

Surveys, usability tests, sales calls, persona writing, market sizing. It differs from the nearby `sourced-market-research` skill in being about primary interviews, not published sources.

## Requirements

Python 3.9 or newer, standard library only, no network. Without Python the agent follows the manual checks in step 6 of the skill.

## Install

To be generated at publication: one pinned command per tool; installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs below are from the saved fixtures, run on 2026-11-21.

1. Prompt: "Check this study file before I present it." Command: `python scripts/jtbd_check.py evals/fixtures/study_good.json`. Result: `"ok": true`, 2 interviews, 5 interviewer questions, 0 leading, 0 errors, 0 warnings; interview I2 has anxiety recorded as `none_found` with a note.
2. Prompt: "Audit this study." Command: `python scripts/jtbd_check.py evals/fixtures/study_bad.json`. Result, exit 1: `"ok": false`, 4 interviewer questions of which 3 leading (`leading_tag`, `hypothetical`, `solution_priming`), interviews B1 and B2 missing forces, statement J1 missing situation and outcome, 19 errors and 5 warnings.

No full agent run with the skill exists yet, so no saved agent transcript is shown.

## Limits

- Question detection is by English wording, not tone.
- The script proves a quote exists in its turn, not that the force label is right.
- 70% talk share, 90-day recall, 6 to 10 interviews are working values.
- Interviews show motive, not market size.

## Evidence

See `VERIFICATION.md`: static lint passed; 6 of 6 script fixture cases pass. Not tested: efficacy against a baseline, triggers, native discovery, any cross-tool run, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run. Planned beats: (1) paste three transcripts; (2) the agent builds the study file; (3) `jtbd_check.py` flags two leading questions and a missing anxiety quote; (4) the agent re-probes or records `none_found`, re-runs to `ok: true`; (5) the job statements appear with their evidence.

## FAQ seeds

1. Does it need network? No.
2. Can it run the interview itself? It scripts and co-pilots; a human talks to the participant.
3. How many interviews do I need? 6 to 10 per segment, stop when two in a row add nothing new.
4. What if a force never comes up? Record `none_found` with the probes used; do not invent a quote.
5. Is it a survey tool? No.
6. What leaves my machine? Nothing; the script only reads the file you name.
7. How do I uninstall? Delete the skill folder.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings; no human review has taken place yet.
