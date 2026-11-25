**Don't keep the skill on this evidence.** Its effect is zero. The colleague's reported +20 points came from grader errors.

**Corrected result (per-output checks, 10 runs per condition):**

| Check | With skill | Without skill |
|---|---|---|
| Correct total | 10/10 | 10/10 |
| Names the duplicate line | 10/10 | 10/10 |
| Doesn't apply a tax rate absent from the file | 4/10 | 4/10 |
| Says USD | 10/10 | 10/10 |
| **Score** | **60%** | **60%** |

The grader reported 80% with the skill versus 60% without. The difference comes from four "with" runs (`6jsw28`, `vbk3a5`, `my88a6`, `uvqvh7`). Each one says "I applied the standard 8% sales tax," yet the grader passed the tax check on all four and gave no supporting quote. Fixing those four removes the whole gap.

**Other problems with the grading:**
- The grader failed the USD check on every other run, even though those runs state USD the same way. I scored it literally, and the result is still 60% vs 60%.
- Every output also says "Amounts appear to be in euros," which contradicts its own USD claim. Nothing in the results settles which currency is right, because the invoice CSVs are not in `results/`.
- The grader gave empty quotes for all of its passes on those four runs, so those verdicts aren't grounded in the text.

**Other observations:**
- The tax behavior depends on the task, not the condition. Tasks 1 and 4 apply 8% tax in both conditions. Task 5 applies none in both. Tasks 2 and 3 flip in opposite directions: the skill adds tax on task 2 and removes it on task 3. The net is zero.
- The two repetitions per cell are almost word-for-word identical. Either the runs are near-deterministic or the reps aren't independent, and two reps can't tell those apart.
- The results don't show whether the skill was actually loaded in the "with" runs. The transcripts and the skill file aren't in this folder, so I couldn't check.

**Recommendation:** Don't ship the skill as it stands. Before deciding, I'd do three things:
1. Re-grade with a rule that requires a quote for every pass, and check the tax line with a script.
2. Confirm the skill loaded in every "with" run.
3. Rerun with more tasks and independent repetitions.

If the tax check still shows no difference, drop the skill.

I didn't modify anything. I can re-grade the 20 outputs with quoted evidence if you want to pin down the currency question, or draft the revised rubric.
