---
name: decision-council
description: Runs a hard choice through a fixed council of five roles (sceptic, operator, finance, customer, long-term), scores the options in a weighted decision matrix with a script that reports sensitivity and ties, and writes a recommendation with reversibility and kill criteria. Use when the user says should I or should we, help me decide, weigh these options, pros and cons, devil's advocate, or is stuck between choices. Do not use for quick low-stakes picks, brainstorming options from nothing, forecasting, or personalised legal, medical, tax or investment advice.
license: Apache-2.0
compatibility: The matrix script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, compute the weighted scores by hand as described in step 4.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Decision council

One opinion on a hard choice is cheap and tends to flatter whatever the user already leans toward. This skill forces five separate angles, each with required outputs, then makes the weighing explicit so that the user can see which assumption the answer rests on. The decision stays the user's: the agent supplies analysis and a recommendation, never the final call.

## Rules that hold throughout

- No invented numbers. Every figure is tagged [given] (the user said it), [assumed] (a stated guess, shown as a range) or [unknown] (with how to find out).
- "Do nothing" and "delay" are always options unless the user rules them out.
- Weights belong to the user. The agent may propose draft weights, marked proposed, but must have the user confirm or change them before reporting a result as the council's finding.
- A veto is not a score. A fact that makes an option unsurvivable (cash below fixed costs, illegal, unsafe) removes the option or becomes a constraint in the recommendation.
- Stakes involving health, legal exposure, tax or investing: run the council on the structure of the choice, say where a licensed professional is needed, and give no personalised advice on those parts.

## Workflow

```
- [ ] 1 Frame the decision
- [ ] 2 Run the five roles
- [ ] 3 Pick criteria and get weights
- [ ] 4 Score and run the script
- [ ] 5 Read the result honestly
- [ ] 6 Write the recommendation
- [ ] 7 Report
```

1. **Frame.** Write four lines: the decision as a question; the options, including "do nothing" and any staged or smaller option; the deadline and who decides; what the user says matters most. Ask at most three questions, only for what is missing and cannot be assumed. If the user supplied options, do not add more than one of your own, and label it as yours.
2. **Run the council.** For each role in this order, write the block defined in [references/roles.md](references/roles.md): sceptic, operator, finance, customer, long-term. Read the card for each role before writing it. Every block covers every option, uses the stance/findings/needs-to-know/confidence format, and adds something the user's notes did not say. If all five agree, re-run the sceptic against the favourite. End with a short "Disagreements" list: where roles pulled in opposite directions and why.
3. **Criteria and weights.** From the council's findings choose four to seven criteria, each one idea with an obvious direction; move any veto out of the matrix and apply it first. Propose weights on a 1 to 10 scale, marked proposed, and ask the user to confirm or change them. See [references/matrix_method.md](references/matrix_method.md) for how to choose criteria and anchor scores.
4. **Score and run.** Score every option on every criterion on one 1 to 5 scale, with one line of evidence per score; mark guesses [assumed]. Save the matrix as JSON or CSV (templates: `assets/matrix_template.json`, `assets/matrix_template.csv`) and run:

```bash
python scripts/decision_matrix.py matrix.json
```

   It prints strict JSON. Without Python, normalise the weights to sum to 1, flip any cost criterion (new score = min + max - score), multiply and add; then for the top two options find, per criterion, the weight at which they swap, and say these were computed by hand.
5. **Read the result.** Use these fields, and say what each means in plain words:
   - `winner` and `margin`: how far ahead, as a percentage of the scale. Under about 5% is noise.
   - `tie_report`: if `exact_ties` or `near_ties` are non-empty, the matrix does not separate those options. Do not pick one. Offer the `resolved_by` criterion, a cheap test, or a smaller reversible step.
   - `sensitivity.label` and `smallest_flip`: if fragile or moderate, name the criterion and the weight at which the winner changes (for example "Risk would have to fall from 3 to 1") and ask the user whether that weight is plausible.
   - `equal_weights_same_winner`: if false, the result depends on the weights; say so.
   - `dominated`: options that can be dropped.
   - `warnings`: relay each one.
6. **Recommend.** Use the shape in `assets/recommendation_template.md`. Rules for the two parts people skip are in [references/reversibility_and_kill_criteria.md](references/reversibility_and_kill_criteria.md): reversibility needs class, cost to undo, window and point of no return; kill criteria need at least two items, each with a measurable signal, a threshold, a check date, an owner and the action when crossed. If the council found a one-way door, recommend the staged first step before the full commitment.
7. **Report** in this order: the framing lines; the five role blocks (condensed to stance and top finding if the user asked for short); the matrix table with scores and the script's verdict; the recommendation; and a closing section:

```
Not checked: <facts the council could not verify, scores that are [assumed]>
Needs a person: <questions for a licensed professional or someone who holds the missing fact>
```

Save the matrix file and the recommendation next to the user's work when they have a folder; otherwise show them in chat.

## Script

`scripts/decision_matrix.py <file>`: run it, do not edit it to change a result. Options: `--near-tie PCT` (default 2) and `--scale MIN,MAX` (default 1,5 or the value in the file). Exit 0: unique winner. Exit 1: first place is tied (output is still valid JSON). Exit 2: input error, with `{"ok": false, "error": ...}` saying what to fix, such as a missing score or a score outside the scale. CSV rows named weight, direction and scale are reserved.

## Limits

- Weighted scoring turns judgement into numbers; it cannot make a poor estimate good. The council's value is in the questions and the exposed assumptions more than in the final score.
- Scores and weights come from the user and the agent's reading of the notes. Nothing is verified against outside sources unless the user supplies them.
- The sensitivity analysis changes one weight at a time, with the rest rescaled in proportion. It does not test two weights moving together or changes to scores.
- The fragile, moderate and robust cut-offs (0.10 and 0.20 shift in normalised weight) and the 2% near-tie gap are working values, not measured optima.
- The five roles are one model playing five parts, not five independent minds. They share the same blind spots; the user's own knowledge is the check.
- Not a substitute for a lawyer, doctor, tax adviser or financial adviser, and it does not predict outcomes.
