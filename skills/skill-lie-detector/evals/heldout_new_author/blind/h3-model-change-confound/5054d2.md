**No. The data can't attribute the gain to the skill, and it doesn't support advertising it as the cause.**

The two arms differ in two ways, not one:

- **Skill:** baseline had no skill; the with-skill runs had it.
- **Model:** baseline used the old model; the with-skill runs used the vendor's newer, more capable model.

The shared checks and input files control for the grading and the content, but not for the model. Any gain could come from the skill, the model, or both. The 20-point difference is the combined effect of both changes. The p-value and interval say the difference is unlikely to be noise. They don't say what caused it.

The timing adds a smaller confound. The arms ran on different days (Monday and Friday), so anything else that changed in that window, such as the grader, the API, or caching, is also uncontrolled.

Eight tasks is also a small sample, so the interval [12,28] is wide and says little about how the skill would do on other contracts.

**What you can claim:** "Across eight contract-summary tasks, the with-skill runs on the newer model scored 20 points higher than the old-model baseline (95% CI [12, 28], p = 0.008)." That is accurate, but it bundles the skill and the model.

**What would isolate the skill:** run the new model without the skill on the same eight tasks, same checks, same inputs, close in time to the with-skill runs. That gives a 2×2 comparison:

| | No skill | Skill |
|---|---|---|
| Old model | baseline (have) | not run |
| New model | needed | have |

- The gap between "new model, no skill" and "new model, with skill" is the skill's effect on the new model.
- The gap between "old model, no skill" and "new model, no skill" is the model's effect.

If you can only run one more arm, "new model, no skill" is the one to run. Ideally, interleave the runs and randomize their order to reduce drift, and add more tasks if the effect needs a tighter interval.

Until that arm exists, the skill is one possible contributor, and the advertising should say that the skill was used alongside the newer model.
