---
name: jobs-to-be-done-interview
description: Prepares, scripts and analyses Jobs-to-be-Done (JTBD) customer interviews. Use when a founder or PM says JTBD interview, switch interview, why did customers switch, interview guide, code my interview transcripts, forces diagram, or write job statements. Covers a timeline question flow, non-leading question rules, push/pull/anxiety/habit coding and job statements, with a script that checks transcript plus coding JSON for leading questions, missing forces and incomplete statements. Do not use for surveys, usability tests, sales calls, persona writing, or market sizing.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only, no network. Without Python, run the manual checks in step 6.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Jobs-to-be-Done interviews

Find out why a person moved from one way of doing something to another, from the story of one real decision. The unit of analysis is the decision, not the person and not the product. Opinions, wish lists and "would you use" answers are not data here.

## Pick the mode first

| User has | Mode | Go to |
|---|---|---|
| A product question and no interviews yet | Prepare | steps 1 and 2 |
| Wants the agent to script or co-pilot the interview | Script | step 3 |
| Transcripts or notes | Analyse | steps 4 to 7 |

Never invent interview content. If the user has no transcripts, produce only the guide and the recruiting screen.

## Workflow

```
- [ ] 1 Define the switch and the screen
- [ ] 2 Write the guide from the timeline
- [ ] 3 Run or script the interview
- [ ] 4 Put transcripts into the study file
- [ ] 5 Code forces with verbatim quotes
- [ ] 6 Run the checker, fix, re-run
- [ ] 7 Synthesise job statements and report
```

1. **Define the switch.** Write one sentence: "People who [moved to / stopped using / chose] X in the last 90 days instead of Y or nothing." Screen participants on a real event with a date, within 60 to 90 days (older memories turn into rationalisation). Include people who tried and dropped it. Plan 6 to 10 interviews per segment; stop adding when two consecutive interviews produce no new push, pull, anxiety or habit. Never recruit people to "give feedback on the idea".
2. **Write the guide.** Use the timeline in [references/interview-guide.md](references/interview-guide.md): 55 minutes, seven phases with minute budgets, 2 to 4 prompts per phase, and the probes for each force. Read only the phases you need to adapt. Output: the guide as a table (phase, minutes, prompts, what to listen for) plus the recruiting screen.
3. **Script or run the interview.** One prompt, then silence; follow the participant's timeline, not the guide order. Questions must pass the rules below. As co-pilot, flag each drafted question that fails a rule before it is asked and give the rewrite. Do not answer for the participant, summarise mid-interview, or mention the product unless the participant does first.
4. **Build the study file.** Turn each transcript into the JSON of [references/synthesis-contract.md](references/synthesis-contract.md) (template: `assets/study_template.json`). One turn per speaker change, numbered from 1, text verbatim. Do not clean up the interviewer's questions: leading ones must stay visible.
5. **Code forces.** Per interview, find at least one participant quote for each of four forces and code it (`push`, `pull`, `anxiety`, `habit`). Definitions are below. Quotes are copied word for word from the turn. If a force really is absent after you probed it, write `none_found` with a note saying what was asked; never invent a quote to fill a gap.
6. **Check.** Run `python scripts/jtbd_check.py study.json`. Fix errors and re-run until `"ok": true`. Warnings (opinion questions, double questions, why-questions, interviewer talking more than 30% of words) go to the user, not hidden. Run it; do not edit it to pass. Without Python, check by hand: every interviewer question against the rules table; every interview against the four forces; every statement for the three parts and two interviews of evidence.
7. **Synthesise and report.** Cluster codes across interviews, write statements by the contract, and report in the fixed shape below.

## The four forces

| Force | Meaning | Listen for | Probe |
|---|---|---|---|
| push | What was wrong with the situation before | A dated moment, a cost, an embarrassment | "What was happening the day you first thought about it?" |
| pull | What the new thing promised | A picture of a better day, seen or heard from someone | "What did you imagine would be different?" |
| anxiety | Fear about the new thing | Doubts about cost, learning, trust, other people | "What gave you pause before you committed?" |
| habit | Comfort with the old way | Workarounds, sunk effort, "everyone knows how it works" | "What was good enough about how you did it before?" |

A switch happens when push plus pull outweigh anxiety plus habit. Count a force once per interview in the summary; the strength is in the evidence quoted, not in how often a word appears.

## Non-leading question rules

The checker detects the patterns marked E (error, fails the file) and W (warning).

| Pattern | Class | Fix |
|---|---|---|
| "Don't you find X frustrating?", "..., right?" | E leading_tag | "How did you handle X?" |
| "You must have been annoyed" | E leading_assumption | "How did you feel at that point?" only after they describe it |
| "Would you use / pay for / switch to..." | E hypothetical | "Tell me about the last time you did switch." Past behaviour only |
| "What if we built...", "imagine..." | E hypothetical | Drop it; interview the past |
| "our product / the app / the feature" | E solution_priming | Name nothing you sell; use their words |
| "Do you think / like / prefer...?" | W opinion_seeking | "What did you do?" |
| "... and how much would you pay?" | W double_barreled | One question per turn |
| "Why did you choose it?" | W why_prompt | "What led up to choosing it?" (why invites tidy reasons) |

Also: do not offer options in a question ("was it price or features?"); do not say "great" or "interesting" after answers; repeat their exact word to continue.

## Report format

```
Study: <switch sentence>, <n> interviews
Leading questions: <count of n questions, rate>, <worst 3 with rewrite>
Forces per interview: <table: interview x push/pull/anxiety/habit = quotes or none_found>
Job statements: <each: When ..., I want to ..., so I can ..., evidence interviews>
Checker: <ok true/false, errors, warnings>
Not checked: <e.g. whether participants match the screen; whether quotes carry the meaning you coded>
```

## Scripts and files

- `scripts/jtbd_check.py <study.json> [--min-evidence N]`: run it. Prints one JSON object: `ok`, `summary` (interviews, interviewer_questions, leading_questions, leading_rate, interviews_missing_forces, statements_missing_parts, errors, warnings), per-interview `forces` and `findings`, per-statement `missing_parts` and `findings`. Exit 0 ok, 1 errors, 2 input problem (the JSON then has an `error` field and no summary).
- `assets/study_template.json`: copy and fill; it is a template, not a passing study.
- `references/interview-guide.md`: read for steps 2 and 3.
- `references/synthesis-contract.md`: read for steps 4, 5 and 7.
- [references/sources.md](references/sources.md): read only when the user asks where the method comes from.

## Limits

- The checker finds question patterns by wording, in English. A leading tone, a nod, or a question that sounds neutral but implies an answer is not caught; read the transcript too.
- Force coverage is counted from your coding. The script proves each quote exists in its turn, not that the force label is right.
- 70% participant talk share, 90-day recall and 6 to 10 interviews are working values, not measured optima.
- Eight interviews show patterns in motive; they do not size a market or prove a feature will sell.
- Interviews can touch employers, health or money: get consent, and store no names beyond what the study needs.
