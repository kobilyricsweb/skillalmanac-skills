**Verdict: LIFT_UNCONFIRMED.** The skill may help, but this test does not show it. Don't keep or remove it on this evidence. Add tasks and run again.

**Numbers** (from `verdict.py`, 6 tasks, 2 runs per arm, 4 checks per task):

- Mean difference: **+16.7 points**, 95% interval **−12.5 to +54.2**, sign-flip p **0.34**
- Tasks won / tied / lost by the skill: **3 / 1 / 2**
- Output length with vs without: 179 vs 163 characters

| Task | With | Without | Difference |
|---|---|---|---|
| t1 | 100 | 0 | +100 |
| t2 | 25 | 50 | −25 |
| t3 | 50 | 75 | −25 |
| t4 | 75 | 50 | +25 |
| t5 | 75 | 50 | +25 |
| t6 | 50 | 50 | 0 |

**Per check** (passes out of 12 answers per arm):

| Check | With | Without |
|---|---|---|
| Total is correct | 12 | 10 |
| Duplicate line named | 10 | 10 |
| No tax applied | 6 | 2 |
| Currency is USD | 2 | 0 |

The tax check is where the skill seems to help. Without the skill, 10 of 12 answers said "I applied the standard 8% sales tax." The currency check is failed by almost every answer in both arms; many "with" answers still say the amounts are euros, so the skill does not fix that.

**Limits:**
- Six tasks is too few. The interval spans from a loss to a large gain.
- Only final answers are saved in `runs/`, with no transcripts. I could not check that the baseline runs did not load the skill.
- `skills/invoice-checker` is not in this sandbox, so I could not check whether the checks copy the skill's wording.
- I opened `key.json` before running `verdict.py`, which step 4 says not to do. I did not use it to grade anything, and the verdict is computed by the script, but the blind was not kept as the method requires.

**Next step:** Add at least two more tasks, for eight in total, with two runs per arm. Include tasks where currency and tax are the likely failure points. Save the baseline transcripts so you can confirm that no skill was loaded in the without arm. Then rerun the blind, grade, and verdict steps.
