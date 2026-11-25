**Recommendation: don't enable it by default for all 500 staff.** Keep it available as an opt-in, or run a larger pilot first.

**Why the benefit isn't established:**
- The 2.5-point gain has a 95% interval of [-1, 6] and p = 0.41. That is what you'd expect from noise on this sample, so the test doesn't show the skill helps.
- The interval also doesn't show it hurts. The true effect could be anywhere from slightly negative to about +6 points, so the data is inconclusive, not negative.
- Eight tasks with two runs each is very little. The interval is probably too narrow, since the real uncertainty about how these tasks generalize is larger than the resampling captures.

**Why the cost is clear:**
- Runtime rises about 6x (15s to 90s). Staff would wait over a minute for each explanation, which is a real usability cost at 500-user scale.
- Answer tokens rise about 4.4x (900 to 4,000). Output tokens are typically the expensive part of a model call, so per-query cost rises by roughly that factor, and the total grows with query volume.

**The trade:** A likely gain of at most a few points, which the data doesn't yet confirm, against a certain 4–6x increase in latency and token spend for every user on every query. Unless each percentage point of pass rate is worth a lot to the business, the default-on cost isn't justified by this evidence.

**What would change my mind:**
- A larger test (more tasks drawn from real staff questions, more runs per task) whose interval's lower bound is clearly above zero and large enough to justify the cost.
- A cheaper variant of the skill that keeps most of the accuracy with far fewer tokens.
- Evidence that the failures it fixes are high-stakes errors, where a small gain matters more.

**Practical next step:** Offer it as an opt-in for the users or task types where a more accurate, slower answer is worth it, and log usage and pass/fail feedback. That collects the larger sample you'd need to decide on default-on later.
