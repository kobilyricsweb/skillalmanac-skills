# Idea scoring matrix

## One line

Ranks scored ideas by weighted total, then checks whether the top idea still wins when any one criterion weight moves by 25 percent in either direction.

## What it does

The skill takes a short list of candidate ideas, each scored from 1 to 5 against a fixed set of criteria, and turns the scores into a ranking. Each criterion carries a positive weight, so the weighted total for an idea is its weighted average score on the same 1 to 5 scale. Ties at the top are reported as ties and broken by idea name, which is stated in the output so nobody mistakes the tie-break for a judgment.

The stability check is the part a plain spreadsheet rarely does. For each criterion, the script multiplies that single weight by 0.75 and then by 1.25, recomputes the ranking, and records whether the winner changed. The result is a list of flips, or a plain statement that the winner held under every shift. The script is a single Python file that uses only the standard library and reads one JSON file.

## When to use

- A brainstorm has produced between two and 200 concrete ideas, and the user has numeric scores for at least two criteria.
- The user wants a shortlist and needs to know whether the order depends on the exact weights.
- A team has agreed on criteria such as impact, feasibility, novelty, and cost, and wants the arithmetic written down so it can be rechecked.

## When not to use

- The task is to generate ideas. This skill only ranks ideas that already exist.
- The criteria have no numbers, or scores are guesses the user has not confirmed.
- There are more than 200 ideas or more than 20 criteria. The script refuses those inputs.

## Requirements

Python 3.9 or later. No third-party packages and no network access. The script reads one input file of at most 2 MB and writes nothing to disk.

## Example

The smoke input has five ideas and four criteria. Running `python -I scripts/score_ideas.py fixtures/sample_5x4.json` from the skill folder produced this stdout (JSON, pretty-printed by the script):

```
{
  "status": "ok",
  "winner": "Weekly idea review",
  "margin_to_runner_up": 0.2,
  "tie_at_top": false,
  "winner_robust": true,
  "ranking": [
    {
      "rank": 1,
      "idea": "Weekly idea review",
      "total": 4.0
    },
    {
      "rank": 2,
      "idea": "Shared scoring board",
      "total": 3.8
    },
    {
      "rank": 3,
      "idea": "Idea marketplace",
      "total": 3.6
    },
    {
      "rank": 4,
      "idea": "Hackathon sprint",
      "total": 3.4
    },
    {
      "rank": 5,
      "idea": "Expert panel",
      "total": 3.1
    }
  ],
  "sensitivity": [
    {
      "criterion": "impact",
      "change": "minus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "impact",
      "change": "plus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "feasibility",
      "change": "minus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "feasibility",
      "change": "plus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "novelty",
      "change": "minus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "novelty",
      "change": "plus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "cost",
      "change": "minus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    },
    {
      "criterion": "cost",
      "change": "plus25",
      "winner": "Weekly idea review",
      "winner_changed": false
    }
  ]
}
```

The same run wrote this table to stderr:

```
Rank  Idea                             Total
1     Weekly idea review               4.000
2     Shared scoring board             3.800
3     Idea marketplace                 3.600
4     Hackathon sprint                 3.400
5     Expert panel                     3.100
Winner: Weekly idea review | robust: yes | tie at top: no
Sensitivity flips: 0 of 8
```

## Limits

- Scores must be integers or decimals from 1 to 5. Anything else is refused with exit code 2.
- The stability check moves one weight at a time by fixed factors of 0.75 and 1.25. It does not test every combination of weights, and it does not test changes to the scores themselves.
- A winner that survives the check can still be a close call. The skill reports margin to the runner-up so the user can judge that.
- The 0.10 close-margin cutoff and the 2 MB and 200-idea limits are working values chosen for this skill, not standards.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
