**No. Don't attribute the gain to the skill or advertise it.** Your facts don't support that claim, and the skill's own method would not accept this comparison as a test of the skill.

**Why:** The skill's first ground rule is that both arms get the same model. Your arms differ in model: the baseline ran on the old model last Monday, and the with-skill runs ran on the newer model on Friday. The 20-point difference therefore measures "new model + skill" against "old model," and the data can't separate the two. The newer model alone could account for some or all of it. The checks and inputs being identical controls for the tasks, not for the model.

**What the statistics do and don't tell you:**
- The interval [12, 28] and p = 0.008 describe the size of the gap between arms. They say nothing about its cause, because the confound sits in the design, not in the sample size.
- With 8 tasks, the smallest exact two-sided sign-flip p is about 0.008, which is what you get when all 8 tasks favour one arm. If that's how p was computed, the newer-model arm won every task. That's a strong difference, but it's still confounded.
- Using the skill's own verdict rules, the design fails the requirement for a valid comparison, so the honest label is INCONCLUSIVE ("an incomplete test"), not LIFT.

**What would settle it:** Rerun with the model held constant:
1. **Same-model comparison (the key test):** run the with-skill and without-skill arms on the newer model, same 8 tasks, 2 reps each, fresh contexts. If the skill helps, the gap should persist here.
2. **Optional:** run both arms on the old model as well. That shows whether the skill's effect depends on the model.
3. **Check for other changes:** the Monday-to-Friday gap could also include other changes (prompt-caching, system prompt, tool versions). Confirm nothing else differed between those dates.

Until step 1 is done, the honest claim is: "Results improved by 20 points after we switched models and added the skill. We have not yet isolated the skill's contribution." I can set up the same-model rerun in `.tools/skill-lie-detector` if you want to proceed. I haven't run anything here, since you asked me to analyze only these facts.
