# Building the decision matrix

## Contents
- Criteria
- Weights
- Scores
- What the script computes
- Reading the sensitivity output
- Known weaknesses of weighted scoring

Read when building or explaining the matrix. Skip for a quick rerun.

## Criteria

- Take them from the council, not from a stock list. A good source is every role's "needs to know" and "top findings".
- Use four to seven. Fewer hides trade-offs; more spreads weight so thin that nothing matters.
- Each criterion is one idea, phrased so that its direction is obvious: "Monthly cost (higher is worse)". Two ideas in one name ("cost and speed") cannot be scored.
- Do not include a criterion that is really a veto. Vetoes (cannot afford it, illegal, unsafe) are gates applied before the matrix: an option that fails one is removed and the reason written down.
- Watch for double counting: "growth potential" and "long-term upside" usually measure the same thing and quietly double its weight.

## Weights

- The decider sets the weights, not the agent. Offer a draft marked "proposed" and ask the decider to change anything. A weight set by the agent is the agent's decision.
- Any non-negative numbers work; the script normalises them to sum to 1. Whole numbers such as 1 to 10 are easiest to discuss.
- Ask the forcing question: "If you could only improve one of these, which?" Order the criteria, then give the numbers.
- Equal weights are a choice, not a neutral default. The script warns when all weights are equal.

## Scores

- Use the same 1 to 5 scale for every criterion. For a benefit, 5 is best. For a cost criterion mark direction "cost" and score the raw level (5 = most costly); the script flips it.
- Write one line of evidence next to every score. A score without a reason is an opinion; mark it [assumed].
- Score all options on one criterion before moving to the next. It keeps the comparison fair.
- Anchor the ends: say what a 1 and a 5 mean for that criterion ("5 = pays back inside 12 months").
- Include "do nothing" as an option. It is the baseline the others have to beat.

## What the script computes

With raw weights w_i, the normalised weight is n_i = w_i / sum(w). For a cost criterion the score s on a scale lo..hi is flipped to lo + hi - s. Option score = sum of n_i times adjusted score. score_pct = (score - lo) / (hi - lo) x 100.

Sensitivity: for each criterion, set its normalised weight to x and rescale all the other weights in proportion so they still sum to 1. Each option's score is then a straight line in x, so the point where a challenger's line crosses the winner's is solved exactly. The nearest crossing is reported both as the normalised weight and as the equivalent raw weight (other raw weights unchanged), plus the shift in normalised points. Labels: fragile if the smallest shift is under 0.10, moderate under 0.20, otherwise robust. These cut-offs are working values.

Tie report: exact ties (scores within 1e-9), near ties (gap under 2% of the scale range, changeable with --near-tie), and, for an exact tie, the highest-weighted criterion on which the tied options differ.

Dominated options score no better than another option on every criterion and worse on at least one; they can be dropped without changing the decision.

## Reading the sensitivity output

- Robust: the winner holds under any single-weight change. The decision turns on scores, so spend the checking effort on the evidence behind the winner's scores.
- Fragile or moderate: the decision turns on a weight. Say which: "Risk would have to fall from 3 to 1 for A to overtake." Ask the decider whether that weight is plausible, and report the answer.
- Equal-weights winner differs from the weighted winner: the result depends on the weights; say so.
- Near tie or tie: the matrix cannot separate the options. Do not pick one for the user. Offer the tie-breaker (the highest-weight criterion where they differ), a cheap test, or a smaller reversible step.
- One criterion above half the weight: the matrix mostly restates that criterion.

## Known weaknesses of weighted scoring

- It assumes criteria add up independently. A fatal flaw cannot be offset by strengths elsewhere, which is why vetoes sit outside it.
- Scores are on an ordinal feel-scale; the arithmetic gives false precision. Differences under about 5% of the scale are noise.
- Option lists are rarely complete. The best choice may be a combination or a fourth option the council surfaced.
- Framing effect: the same facts scored by a different person can rank differently. If the margin matters, have the decider rescore the two closest options without looking at the first scores.

Source, in the author's own summary: the technique is standard multi-criteria decision analysis (weighted-sum model and its sensitivity to weights), described at https://en.wikipedia.org/wiki/Multiple-criteria_decision_analysis.
