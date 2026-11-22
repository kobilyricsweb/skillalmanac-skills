# Listing page content: consulting-style-analysis

**One line:** Structures a business question into an issue tree, hypotheses, sourced evidence and an answer-first memo, with a checker.

## What it does

The skill gives an agent a fixed eight-step procedure: frame the question, write a first answer before researching, build an issue tree whose MECE-ness is checkable through declared tags, attach a falsifiable hypothesis to each leaf, record evidence rows with source, source type and a 0-to-1 confidence, validate, then write the pyramid memo. A script validates the tree, hypotheses, evidence, summary and sections from one JSON file and prints strict JSON. A reference gives splitting rules for common question types, a confidence rubric with ceilings per source type, and examples of weak and strong so-what lines.

## Capabilities

- `scripts/analysis_check.py check`: finds overlapping or non-exhaustive branches (by declared tags), hypotheses without evidence or a falsifier, evidence without a source, confidence outside 0 to 1 or above the ceiling for its source type, summaries over 150 words, sections without a so-what line
- `scripts/analysis_check.py template`: prints a valid skeleton input
- A fixed final report: answer, tree check, evidence quality, change from the first answer, what was not checked

## When to use

You want a structured analysis, an issue tree, a MECE breakdown, a hypothesis-driven approach or a pyramid-principle memo for a business question ("why did margin fall", "should we enter this market").

## When not to use

Picking between options by debate (see `decision-council`), stress-testing a plan (see `plan-stress-test`), mapping claims in an existing document to evidence (see `claim-evidence-map`), open-ended cited research, or crunching a dataset. How it differs: this skill produces the analysis deliverable and checks its structure; the others review a decision, a plan or a document.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent follows the manual checks in the skill.

## Install

To be generated at publication: one pinned command per tool.

## Examples

Real fixture runs of the script (`python evals/run_fixtures.py`, 6/6 pass):

1. `python scripts/analysis_check.py check evals/fixtures/good.json` -> `"ok": true`, 7 nodes, 4 leaves, 4 hypotheses, 5 evidence rows, 85-word summary, no errors or warnings. Exit 0.
2. `python scripts/analysis_check.py check evals/fixtures/bad_tree.json` -> `"ok": false` with `tree-overlap` (tag `online` owned by two branches), `tree-tag-unknown` (`franchise`) and `tree-gap` (`catalog` owned by no branch), plus two `leaf-no-hypothesis` warnings. Exit 1.

No with-skill agent run exists yet, so there is no saved memo to show.

## Limits

- MECE is checked only through the tags the author declares.
- Confidence scores are rubric judgements, not probabilities.
- The script does not read sources or verify numbers; passing means sound structure, not a correct conclusion.
- Word counts split on spaces.

## Evidence

See `VERIFICATION.md`. Static lint passed; 6 script fixture cases pass. Not tested: with/without efficacy, trigger behaviour, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run. Planned beats: (1) paste churn notes and ask for an analysis; (2) the agent states a first answer and shows the tagged tree; (3) `check` flags an overlap, the agent fixes it; (4) the memo opens with the answer and a 150-word summary, every section ends with a so-what.

## FAQ seeds

- Does it need network? No.
- How is it different from decision-council or plan-stress-test? Those judge a decision or a plan; this builds the analysis itself.
- Can the script tell me my conclusion is right? No, only that the structure is sound.
- Why declare tags? So overlaps and gaps can be detected mechanically.
- What if I have no data? Rows become assumptions with confidence 0.4 or less and are reported as such.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft, not re-verified.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review yet.
