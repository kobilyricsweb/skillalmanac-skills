## Contents

1. Study file shape
2. Coding rules
3. Job statement contract
4. From codes to statements, in order
5. Checker findings and what to do

## 1. Study file shape

One UTF-8 JSON object.

```
{
  "study": "<switch sentence>",
  "interviews": [
    {
      "id": "I1", "participant": "P1",
      "turns": [ {"n": 1, "speaker": "interviewer|participant", "text": "..."} ],
      "codes": [
        {"force": "push|pull|anxiety|habit", "turn": 2, "quote": "verbatim part of turn 2"},
        {"force": "anxiety", "none_found": true, "note": "what was probed, at least 4 words"}
      ]
    }
  ],
  "job_statements": [
    {
      "id": "J1",
      "situation": "...", "motivation": "...", "outcome": "...",
      "text": "When <situation>, I want to <motivation>, so I can <outcome>.",
      "evidence": [ {"interview": "I1", "turn": 2}, {"interview": "I2", "turn": 4} ]
    }
  ]
}
```

`job_statements` may be empty until synthesis starts; the checker then adds the warning `no_job_statements`. Turn numbers are unique inside an interview. Interview ids are unique across the file.

## 2. Coding rules

1. Code only participant turns. A force named by the interviewer is not evidence.
2. The `quote` is a verbatim part of the turn (whitespace and case are ignored). Do not repair grammar, do not join two sentences with "...".
3. One code, one force. If a sentence holds two forces, make two codes with different quotes from it.
4. Push is about the old situation, pull about the new option, anxiety about the new option's risks, habit about the old way's comfort. Quick test: if the quote would still be true had the participant never heard of the new option, it is push or habit; if it is about the new option, it is pull or anxiety.
5. `none_found` is allowed per force per interview, only with a note naming what was asked. Three or more `none_found` in one interview means the interview did not reach the decision; mark it for re-interview rather than analysing it.
6. Never code a hypothetical ("I would probably...") as a force; it is not a past event.

## 3. Job statement contract

Form: `When <situation>, I want to <motivation>, so I can <outcome>.`

| Part | Content | Test |
|---|---|---|
| situation | The circumstance that triggers the need, in the participant's terms | A person outside your product category recognises it |
| motivation | What they want to be able to do, as an action | Contains no product, feature or tool type |
| outcome | The progress they are after, as a result they can notice | Stated as a change in their life or work, not as a metric you sell |

The checker requires: each part at least 3 words; `text` starts with "When", contains "I want to" and "so I can", and contains the three parts verbatim; evidence from at least 2 different interviews (override with `--min-evidence`); every evidence reference points to a real turn; a warning when the text names a solution type (app, tool, software, feature, platform, dashboard, integration, plugin, extension, subscription).

Statement quality beyond the checker:
- Competitor test: could a product from a different category satisfy it? If not, it is a feature in disguise.
- Size test: one statement per distinct situation. "When X, I want to A and B and C" is three statements.
- Rank statements by number of interviews that support them, not by the number of quotes.

## 4. From codes to statements, in order

1. List every push code by interview, one line each, with the date or event in the quote.
2. Group pushes that share a situation. A group needs 2 or more interviews to become a candidate.
3. For each candidate, read the pull codes of the same interviews: what picture of progress did they share? That is the motivation and outcome.
4. Write the statement; cite one turn per supporting interview.
5. Attach the strongest anxiety and habit codes to the statement as the blockers a solution must overcome. Report them beside the statement; they are not part of `text`.
6. Run the checker. Statements that fail on `thin_evidence` are hypotheses: report them as such, do not drop them silently.

## 5. Checker findings and what to do

| Rule | Severity | Action |
|---|---|---|
| leading_tag, leading_assumption, hypothetical, solution_priming | error | Report the question, give the rewrite; the answer that followed is weak evidence, do not code it |
| opinion_seeking, double_barreled, why_prompt | warn | Report; keep the coding if the participant answered with a past event |
| interviewer_dominates | warn | Participant under 70% of words; consider whether the interview reached a real story |
| force_not_covered | error | Find a quote, or probe again, or record none_found with a note |
| code_on_interviewer_turn, quote_not_in_turn, code_turn_missing, unknown_force, none_found_without_note | error | Fix the coding |
| missing_part, text_not_in_form, part_not_in_text | error | Rewrite the statement |
| thin_evidence, bad_evidence_ref | error | Add real support from another interview or mark the statement a hypothesis in the report |
| solution_in_statement | warn | Rewrite without the solution word unless the participant's situation itself is about it |
