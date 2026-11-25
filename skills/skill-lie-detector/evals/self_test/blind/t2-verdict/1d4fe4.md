**Short answer: the evidence doesn't show that the skill helps.** Its measured advantage comes from one task (t1). Across the other five tasks, with and without the skill score the same.

**Scores (grades.json mapped through key.json, 4 checks per task)**

| Task | With skill | Without skill |
|---|---|---|
| t1 | 4/4 | 0/4 |
| t2 | 1/4 | 2/4 |
| t3 | 2/4 | 3/4 |
| t4 | 3/4 | 2/4 |
| t5 | 3/4 | 2/4 |
| t6 | 2/4 | 2/4 |
| **Total** | **15/24 (62.5%)** | **11/24 (45.8%)** |

The raw files show 30/48 vs 22/48, but that double-counts. Each run was graded twice (see below).

**Per check, across the 6 tasks:**
- Total correct: 6/6 with, 5/6 without
- Duplicate line named: 5/6 with, 5/6 without
- No tax applied when the file has none: 3/6 with, 1/6 without
- Currency stated as USD: 1/6 with, 0/6 without

**Where the difference comes from:** Without t1, both arms score 11/20 (55%). The 4-check gap is entirely t1. The skill also wins t4 and t5 by one check each, but loses t2 and t3 by one check each, and ties t6. That is three tasks better, two worse, one tied.

**Problems with the test itself:**
- **The two reps are identical.** For every task and arm, `with_1.md` and `with_2.md` (and the `without` pair) are byte-identical, so there are only 6 distinct outputs per arm. The "reps: 2" setting added no information. Either the harness reused one output or the runs are deterministic. Check this before trusting any rerun.
- **Six tasks is a small sample.** One task drives the result, so this can't separate the skill from noise.
- **I couldn't check the expected answers.** The invoice CSVs aren't in `results/`, so I took the keys in `tasks.json` as correct. The "euros" claim in almost every run versus "USD" in the key is the kind of thing to confirm against the inputs.
- **I couldn't confirm the skill was loaded.** The run files are only final answers. If the with-arm never read `skills/invoice-checker`, the comparison is meaningless. Check the transcripts for that.

**Recommendation:** Treat this as "no reliable benefit yet." Before deciding whether to keep the skill, verify that the with-arm actually loaded it, make the reps independent, and add more tasks, especially ones where the skill's rules (tax, currency, duplicates) are tested directly.
