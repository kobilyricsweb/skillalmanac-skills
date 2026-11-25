**Don't keep the skill on this evidence.** The reported win is a grading error. Once the grades are corrected, the skill and the no-skill arm are tied on the one behavior it targets: about 6 of 10 runs in each arm invented an 8% sales tax the file doesn't list.

**What the grader reported**

| | With skill | Without skill |
|---|---|---|
| Overall checks passed | 32/40 (80%) | 24/40 (60%) |
| "Does not apply a tax rate not in the file" | 8/10 | 4/10 |

**What I found when I checked the grades against the outputs**

- **Four grader entries are unsupported.** `6jsw28`, `vbk3a5`, `my88a6` and `uvqvh7` (all "with" arm) are marked pass on all four checks with empty quotes. Their text says "I applied the standard 8% sales tax", so the tax check should fail. Corrected, the with arm passes 4/10 on the tax check, the same as without.
- **Tax-invention counts match across arms.** Applied 8% tax: with skill 6/10 (t1 2/2, t2 2/2, t3 0/2, t4 2/2, t5 0/2); without skill 6/10 (t1 2/2, t2 0/2, t3 2/2, t4 2/2, t5 0/2). The per-task pattern is different in each arm, which looks like run-to-run noise rather than an effect of the skill.
- **Totals and duplicate lines are identical across arms** (all 20 outputs), so they can't separate the arms. I couldn't verify them against the invoices because the CSVs aren't in `results/`.
- **Currency check is ill-posed.** Every output says "USD" and then "Amounts appear to be in euros." The grader failed most of these, and passed the four unsupported entries. Whichever way you score it, it's the same for both arms, so it doesn't change the comparison.
- **Blinding leaks the arm.** Blind files are verbatim copies of the runs, so with-skill outputs open "Here is my check of the invoice." and without-skill outputs open "I read invoice_N.csv." The key is consistent with that split, so the grader could have identified the arm from the first line. The skill was clearly loaded in the with arm, but the substance didn't change.
- **Sample size is small.** Five tasks × two reps per arm is too few to detect a moderate effect. "No measured effect" is the accurate conclusion, not "proven useless."

**Recommendation**

Don't keep the skill as it stands. The tax rule it appears to exist for isn't being followed in 6 of 10 runs. Before deciding again:

1. Re-grade all 40 checks from quotes, with the grader required to quote the supporting line for every pass.
2. Strip the opener so the grader can't tell the arms apart.
3. Clarify the currency check (USD vs euros) and fix it in the rubric.
4. Run more reps (e.g. 10 per task) and check whether the skill's tax instruction is explicit enough.

I couldn't read the skill itself (`skills/invoice-checker`) because it isn't in this sandbox, so I can't say why its tax instruction isn't taking effect. I also didn't modify any files.
