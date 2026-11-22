# Listing page content: decision-council

**One line:** Runs a hard choice past five fixed roles, scores it in a weighted matrix and writes a recommendation with kill criteria.

## What it does

The skill gives an agent a seven-step procedure for a hard decision. It frames the choice (always including "do nothing"), runs five roles in a fixed order (sceptic, operator, finance, customer, long-term) with required outputs and a shared block format, turns the findings into four to seven criteria, and asks the user to confirm the weights. A script then computes weighted scores from a JSON or CSV matrix and reports, as strict JSON, how far ahead the winner is, the weight change on each criterion at which another option overtakes it, whether equal weights give the same winner, any ties and near ties, and dominated options. The final write-up must state reversibility (class, cost to undo, window, point of no return) and at least two kill criteria with threshold, date, owner and action.

## Capabilities

- `scripts/decision_matrix.py`: JSON or CSV in, strict JSON out: ranking with per-criterion contributions, margin, tie report with tie-break criterion, per-criterion sensitivity (flip weight in normalised and raw units), robustness label, equal-weights check, dominated options, warnings
- Five role cards with required outputs and evidence tags ([given], [assumed], [unknown])
- Matrix templates (JSON, CSV) and a recommendation template
- A reference on reversibility classes and on writing kill criteria that someone else can check

## When to use

You say should I or should we, help me decide, weigh these options, pros and cons are not enough, play devil's advocate, run a pre-mortem, or you hold a scored matrix and want to know how safe the winner is.

## When not to use

Low-stakes picks (a laptop colour, tonight's dinner); inventing options from nothing (brainstorming); forecasting; personalised legal, medical, tax or investment advice (the skill states where a professional is needed and does not give that advice).

## How it differs from nearby skills

`decision-evidence-ledger` (batch 03) records a decision and the evidence behind it after the fact. This skill produces the analysis before the decision: roles, matrix, recommendation, kill criteria. The two combine naturally (this skill's output can be logged in a ledger) but neither requires the other.

## Requirements

Python 3.9 or newer for the matrix script (standard library only). No network. Without Python the agent computes the weighted scores by hand, as the skill describes.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved council transcript. What exists is the script on saved fixtures, run on 2026-11-21:

1. `python scripts/decision_matrix.py evals/fixtures/vendor.csv` (three vendors, four criteria, weights 4/3/3/5, cost criteria flipped): exit 0. C wins with 4.0667 of 5 (76.67%), A 3.8, B 3.3333; margin 0.2667 (6.67% of scale); label moderate. The smallest flip is Risk: if its weight falls from 3 to 1, A overtakes C. Raising Cost from 4 to 8 also flips it. Equal weights give the same winner. Each flip was checked by hand and by a separate brute-force search.
2. `python scripts/decision_matrix.py evals/fixtures/tie.csv`: exit 1. X and Y tie at 4.0, Z last at 2.5 and dominated by both. The tie report names Impact (the highest-weighted criterion on which they differ) as the tie-break, favouring Y. The sensitivity section is marked tied.
3. `python scripts/decision_matrix.py evals/fixtures/near.json`: exit 0. Q leads P by 0.1667 on a 1 to 10 scale (1.85% of the scale), reported as a near tie; label fragile, because Growth 2 to 2.5 or Fit 1 to 0.8 hands the lead to P.

## Limits

- Weighted scoring cannot make a poor estimate good; the value is in the questions and the exposed assumptions.
- Scores and weights come from the user and the agent's reading of the notes; nothing is verified externally.
- Sensitivity changes one weight at a time; not two together, and not scores.
- Robustness cut-offs and the 2% near-tie gap are working values.
- Five roles are one model playing five parts and share blind spots.
- Not legal, medical, tax or investment advice; does not predict outcomes.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN; 8 of 8 script fixture cases pass with hand-checked expected output. Not tested: any with/without efficacy comparison of the council procedure, trigger behaviour in any tool, native discovery, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. The user pastes notes about a job offer, a promotion that may come and a freelance idea.
2. The five role blocks appear, each with a stance on every option; the sceptic's pre-mortem names the load-bearing assumption.
3. The agent proposes weights and asks to confirm; the script runs and reports the winner, margin, and "Risk would have to fall from 3 to 1 for the other option to win".
4. The recommendation shows reversibility (point of no return) and two kill criteria with dates and owners.

## FAQ seeds

- Does it decide for me? No. It recommends; you confirm the weights and you decide.
- Does it need network access? No.
- What if my matrix has a tie? The script reports it and the skill tells the agent not to pick arbitrarily.
- Can I give it my own matrix instead of running the council? Yes; the script works on a JSON or CSV file alone.
- Are five roles really five perspectives? They are one model in five roles, so the user's own knowledge is the check; the skill says so.
- How is it different from asking "give me pros and cons"? It requires specific outputs per role, evidence tags, a matrix with sensitivity and a recommendation with kill criteria. No comparison run has been done yet.
- Does it give financial or legal advice? No; it flags where a professional is needed.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## Differentiators (fix round 2026-11-21)

- Versus `decision-evidence-ledger`: that skill records evidence behind a decision; this one runs the five-role council, the weighted matrix and the recommendation with kill criteria.
- Versus `plan-stress-test`: pre-mortem of a written plan belongs there; it is no longer a trigger here.
- The Amazon shareholder-letter URL in the references returned HTTP 200 on 2026-11-21.
