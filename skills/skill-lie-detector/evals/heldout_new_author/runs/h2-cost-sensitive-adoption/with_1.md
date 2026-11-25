**Decision: don't enable it by default for 500 staff.** Keep it available as an opt-in, and run a larger test before deciding on default.

I read the skill's SKILL.md and its `references/formats.md`, then applied its verdict rules to your numbers. I didn't run a new test or `verdict.py`, since there are no grade files to run it on.

**Verdict: LIFT_UNCONFIRMED.** The mean is above zero (+2.5 points), but the 95% interval runs from -1 to +6, so it includes zero, and p = 0.41. The skill's rules call this "maybe helps; add tasks to decide." It is not evidence of a gain.

**Why not default:**

- **The benefit is uncertain.** The plausible range runs from a 1-point loss to a 6-point gain. Eight tasks with two runs each is the skill's minimum for acting on a null result, not enough to confirm a gain.
- **The cost is large and certain.** Per answer, runtime goes from 15 to 90 seconds (about 6x) and answer tokens from 900 to 4,000 (about 4.4x).
- **Per 1,000 answers, the trade is roughly:** +25 correct answers (within a range of about -10 to +60), against about 21 hours of added waiting and about 3.1 million extra output tokens. Your real volume and the cost of a wrong invoice explanation decide whether that is worth it, but the default setting would impose it on every staff query.

**Limits of this reading:**

- I only have the aggregate numbers. Per-task results, the checks, and the grades weren't supplied, so I can't say which tasks drove the lift or whether it came from checks the skill's wording rewards.
- The extra length could explain part of the gain, since longer answers can cover more checks. The per-task grades would show whether that is so.
- The test measured content on invoice-explanation tasks only, and the skill's own method notes it does not test whether the skill triggers on its own.

**Next step:** Offer the skill as opt-in for invoices where a wrong explanation is costly. Then expand the test to 16 or more tasks, with a mix of easy and hard cases and a length-matched check, and decide on the default from that. Pick the 90-second runtime as a fixed cost to weigh, not as something to hide. If you send the per-task grades, I can run `verdict.py` on them to confirm the figures.
