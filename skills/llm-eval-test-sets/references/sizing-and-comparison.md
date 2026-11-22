# Sizing a test set and comparing two runs

## Contents

1. Width of the 95 percent interval by set size
2. Sign test for comparing two runs
3. Hallucination metrics for unanswerable cases
4. Method notes

## 1. Width of the 95 percent interval by set size

Full width (upper bound minus lower bound, in percentage points) of the Wilson score interval for a pass rate, computed for the true pass rate shown.

| Cases | Pass rate 50% | Pass rate 80% | Pass rate 95% |
|---|---|---|---|
| 20 | 40 | 34 | 23 |
| 30 | 34 | 28 | 20 |
| 50 | 27 | 22 | 12 |
| 100 | 19 | 16 | 9 |
| 200 | 14 | 11 | 6 |
| 400 | 10 | 8 | 4 |

Reading it: with 30 cases an observed 80 percent could be anywhere from about 63 to 91 percent. A change of 5 points between two runs on 30 cases is noise. The intervals of two runs overlapping does not prove there is no difference, and non-overlap is not required for one; use the paired test below instead.

Rule of thumb used by the validator: below 30 cases, warn. For a decision between two prompt versions, aim for 100 or more cases or, failing that, repeat the same cases only if the model's output varies between runs.

## 2. Sign test for comparing two runs

Run both versions on the same cases. Count only the discordant cases: A passes and B fails, or B passes and A fails. Cases where both pass or both fail carry no information about which is better.

Exact two-sided sign test (binomial, p = 0.5). Smallest split of the discordant cases that gives p below 0.05:

| Discordant cases | Needed in one direction | The other direction | p |
|---|---|---|---|
| 6 | 6 | 0 | 0.031 |
| 8 | 8 | 0 | 0.008 |
| 10 | 9 | 1 | 0.022 |
| 12 | 10 | 2 | 0.039 |
| 15 | 12 | 3 | 0.035 |
| 20 | 15 | 5 | 0.041 |
| 30 | 21 | 9 | 0.043 |
| 50 | 33 | 17 | 0.033 |

Examples: 12 cases fixed and 3 broken is 15 discordant with a 12-3 split, p about 0.035: a real improvement. 8 fixed and 5 broken is 13 discordant and is not significant. Fewer than 6 discordant cases can never reach p below 0.05, so say "no evidence of a difference" rather than "no difference".

Report the broken cases by id even when the net is positive; a fix that breaks adversarial cases may be a worse trade than the pass rate shows.

## 3. Hallucination metrics for unanswerable cases

Split the set into answerable and unanswerable cases and report two rates, not one:

- Hallucination rate: share of unanswerable cases where the system gave a confident answer instead of abstaining. Lower is better.
- Over-refusal rate: share of answerable cases where the system abstained. Lower is better.

A system that always abstains has a hallucination rate of 0 and a useless over-refusal rate of 100 percent, so the two are always read together. Unanswerable cases need at least 10 percent of the set (the validator warns below that); with fewer than 10 such cases the rate has an interval wider than 25 points.

Good unanswerable probes: facts about private context the model has no access to; events after the model's knowledge limit; questions with a false premise ("when did the company win the 2019 award" when it never did); questions that require a document that was not supplied; precise figures that nobody publishes. A probe is only valid if a careful human with the same information would also decline, so have a second person confirm each one.

## 4. Method notes

- Wilson score interval: the standard improvement over the normal approximation for proportions near 0 or 1 and small n; see the description at https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval.
- Sign test: exact binomial on discordant pairs, described at https://en.wikipedia.org/wiki/Sign_test.
- Both tables were computed for this skill with the standard formulas; they assume cases are independent. Cases written from one template, or several questions about one document, are not independent and make the intervals look narrower than they are.
