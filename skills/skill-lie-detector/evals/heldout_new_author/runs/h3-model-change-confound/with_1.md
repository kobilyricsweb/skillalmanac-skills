**No. Don't attribute the gain to the skill or advertise it.** The comparison is confounded, and the skill's own method rules this design out.

- **The arms differ by model.** The baseline used the old model, and the with-skill runs used the newer one. The skill's method requires the same model in both arms, so the only difference between arms is the skill. Here the model changed too. The 20-point gap is the combined effect of the skill and the model upgrade, and these facts can't separate the two. The model alone could account for all of it.
- **The statistics measure the combined change.** The interval [12, 28] and p = 0.008 describe the difference between the two arms, so they inherit the confound. A tighter interval or smaller p doesn't help, because the bias is in what's being compared, not in the noise.
- **The p-value is consistent with a uniform shift.** On 8 tasks, the smallest possible two-sided sign-flip p is 2/256 ≈ 0.008. So this result is what you'd see if all eight tasks moved the same way, which is what a model upgrade would also produce. Check the per-task table to confirm.

What the facts do support: the same tasks, checks and input files were used, so the task set is not the confound. The accurate claim is "the newer model with the skill scored 20 points higher than the old model without it."

To test the skill itself, keep the model fixed:
1. Rerun the baseline (no skill) on the **newer** model, in fresh contexts, with 2 runs per task and the same checks.
2. Confirm the baseline runs never loaded the skill.
3. Blind and grade both arms with a fresh grader, then compute the difference.

If the with-skill vs. no-skill gap on the new model stays near 20 points, the skill has a real lift. If it shrinks toward zero, the gain came from the model. I haven't run anything, since you asked me to analyze only these facts.
