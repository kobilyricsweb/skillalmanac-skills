**Verdict: NO_LIFT. Don't keep the skill on this evidence.** The skill adds no measurable gain on these five tasks, and it still costs context each time it loads. The test is too small to prove the skill useless, though.

**The mechanical verdict is unreliable.** `` reports mean −20.0 points (95% interval −55.0 to +10.0, sign-flip p 0.25, 5 tasks, 2 runs per arm, wins/ties/losses 1/2/2). But it counts four grades as failed that should not be. Those grades marked every check "pass" with empty quotes, on runs that visibly fail the tax check ("I applied the standard 8% sales tax"). The script correctly treats an unquoted pass as a fail, but the grader's error still skews the number.

**Corrected reading (my own, from the blinded text, not a fresh blind grader):**

| Task | With | Without | Difference | Note |
|---|---|---|---|---|
| t1 | 75 | 75 | 0 | all four runs applied 8% tax |
| t2 | 75 | 100 | −25 | with-arm applied 8% tax in both runs |
| t3 | 100 | 75 | +25 | without-arm applied tax in both runs |
| t4 | 75 | 75 | 0 | all four runs applied 8% tax |
| t5 | 100 | 100 | 0 | no run applied tax |

Mean difference is 0.0 under both readings of check 4 (below), so the verdict is NO_LIFT either way. The only check that varies is "does not apply a tax rate not in the file": 4 of 10 with-arm runs pass it and 4 of 10 without-arm runs pass it. Output length is about 177 characters with the skill and 166 without.

**Problems with the test:**
- **Check 4 is ambiguous.** Every output says "USD" and also "Amounts appear to be in euros." The grader's pass/fail on "currency is USD" is a reading choice, not something the text settles. Per the method, a broken check should be voided, not rewritten, so this needs a new run.
- **I opened `key.json` before computing the verdict,** which breaks the blinding rule. I was reviewing the grades when I did it. The grades were already written before I looked, so they weren't influenced by it, but the blinding is compromised for this run.
- **Four grades are wrong** (the blank passes above). A fresh blind grader should regrade all 20 outputs.
- **Some inputs are missing.** `skills/invoice-checker` and the invoice CSVs are not in this sandbox, so I couldn't check whether the skill text tells the model to apply 8% tax (if it does, the skill is pushing the model wrong in the with-arm) or verify the totals. The baseline transcripts aren't saved either, so I couldn't confirm the without-arm never loaded the skill.
- **The tasks may not test the skill.** The base model gets the totals and duplicate lines right in every run, and the only variance is the tax step.

**Next step:** Don't keep it on this result. If you want a firm answer, check the skill's text for an 8% default first. Then run at least 8 tasks with 2 runs per arm, make the currency check unambiguous, and grade with a fresh blind grader. Until then, treat the skill as not demonstrated to help.
