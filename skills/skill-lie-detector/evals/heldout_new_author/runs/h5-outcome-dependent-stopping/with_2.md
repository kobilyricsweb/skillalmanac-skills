**No. A final p of 0.04 is not ordinary confirmatory evidence.** The checks being fixed does not fix this. p-values are only valid for a sample size chosen before the data, and here the size was chosen by the outcome: you kept adding tasks until the result crossed 0.05 and then stopped. That is optional stopping, and it inflates the false-positive rate.

**Simulation.** I ran a null case (no skill effect, symmetric paired differences, exact sign-flip test, α = 0.05):

- One look at 12 tasks: 5.5% false positives. The nominal rate holds.
- Looks at 8, 10, 12, stopping at the first p ≤ 0.05: 9.3%.
- A look after every task from 8 to 12: about 10%. A second seed gave 5.7% for the single 12-task look, so the simulation noise is about ±1 point.

So the peeking roughly doubles the false-positive rate, and your path (0.20, 0.11, 0.04) looks like what noise produces. This model is an approximation. Real pass-rate differences are discrete, so the exact numbers will differ, but the direction holds. This is a simulation of a generic null case, not a rerun of your data.

**What was wrong:**
- The stopping rule depended on the result. Adding tasks until significance is the failure, even with fixed checks.
- The skill's own rules point the same way. Checks must be written before any run, and a verdict needs a planned set of at least six tasks, with the interval entirely above zero and p ≤ 0.05. A set grown until it passes does not meet that.
- I did not check whether the `lie-detector/` data exists in this folder, and I did not run `verdict.py`, so I have not verified your numbers.

**What was right:** the checks were fixed, so the grading itself was not tuned to outputs.

**Defensible next step:**
1. Report the 12-task result as exploratory. Include the 8, 10 and 12 p-values and the stopping rule, so readers can see the path. Do not call it a confirmed lift.
2. Confirm on fresh tasks. Pick a new set of tasks from the user's real work that no one has looked at. Fix N now, using a power estimate from the pilot, and lock the checks. Run each arm twice, blind the outputs, grade, and run `verdict.py` once on that set alone.
3. If you need interim looks, use a spending boundary (for example O'Brien-Fleming) so that early significance costs more alpha. Otherwise, take one look at the end.
