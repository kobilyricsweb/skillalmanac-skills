**No, don't deploy on the strength of the average.** Under the release plan you preregistered, this is a failed gate, not a close call.

**Why the average doesn't decide it**

- The plan made zero canary disclosures a hard requirement. The average improvement answers a different question: whether the skill helps on task scores. It says nothing about whether the requirement is met.
- The with-skill arm produced one disclosure, and you kept that run in the scores, which was correct. The baseline produced none. As written, the plan's criterion is violated.
- The +10 points, p = 0.02 result is real evidence of a score gain, but a gain on task scores can't offset a constraint the plan defined as absolute.

**What the data does and doesn't show**

- I can't call this a confirmed harm. One event in ten runs doesn't establish that the skill causes disclosure, and the baseline's zero is also weak evidence, since zero in ten runs is consistent with a true rate of roughly 0–30%.
- The rate estimate is wide: 1 of 10 gives a 95% interval of about 0.3% to 45%. The data is compatible with a rare leak or a common one. It can't tell them apart.
- That uncertainty cuts against deploying too. The constraint is there for exactly the case where you can't rule out a leak.

**What I'd do**

1. **Hold the release.** Record the result as a gate failure under the preregistered criteria.
2. **Investigate the disclosure.** Read the transcript and find out why the canary surfaced: did the skill's instructions pull the string into the answer, or did the model reproduce it from context? If the cause is clear, a targeted fix to the skill is the cleanest path.
3. **Test the fix and the disclosure rate together.** Rerun the canary-exposing tasks, with more runs per arm, and report disclosures separately from task scores.
4. **Only then decide.** If the disclosure is reproducible and the fix doesn't work, don't ship. If the fix holds across enough runs that the rate is demonstrably low, the decision can go forward under the original gate.

**Not an option:** lowering the threshold or reclassifying the disclosure as an acceptable tradeoff now, after seeing the result. That would turn the preregistration into a post-hoc rationalization. If the team wants a different standard, the change needs to be made openly, documented as an amendment, and approved by whoever owns the release plan.
