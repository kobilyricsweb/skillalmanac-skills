# Test plan: does the json-records-to-csv skill make the agent better?

I read `SKILL.md`, `LISTING.md`, `scripts/json_to_csv.py` and the fixture. I ran nothing. First, check that the copy you're testing is the same one your team installed (hash the folder).

## My prediction, to be tested

The script does the core work (flatten, join, write CSV) in about 150 lines of stdlib Python. A capable agent with no skill can write something similar in seconds. So I expect the skill's measurable value to come from its guardrails and conventions, not from conversion accuracy: refusing to overwrite, refusing to unwrap a top-level object, disclosing skipped items, flagging blank columns, the 2 MB cap, and CRLF/UTF-8 output. If that's right, the verdict will likely be "dead weight for conversion, possibly useful for guardrails." The test should confirm or refute that, not assume it.

## Arms

| Arm | Setup | Question it answers |
|---|---|---|
| A. Baseline | Agent with the same tools, skill not installed | What does the agent do unaided? |
| B. Full skill | Team's installed folder as-is | What does the team actually get? |
| C. Script only | Skill folder with `SKILL.md` removed, script kept | Is the value in the prose or the code? |

The prompt must never mention the skill. Keep `LISTING.md` out of arm B's visible files, because its worked example is an answer key the agent could copy.

## Stage 1: tool-only tests (no LLM, day 1)

This is the gate. The repo says "Not independently verified," so check the script before judging the agent.

1. **Spec oracle.** Write a reference converter from the `Conversion rules (fixed)` section of `SKILL.md` only. Don't read `json_to_csv.py` while writing it. Hand-verify its output on the fixture. The LISTING example is consistent with the spec on my reading, but check it yourself.
2. **Fuzz diff.** Generate about 1,000 random arrays of objects (nesting, arrays of scalars/objects/arrays, nulls, empty containers, unicode, unequal array lengths). Run both converters in join and row mode, and diff the CSV cells and header. Any difference is either a spec gap or a bug; sort them by hand.
3. **Exit-code and reason table.** One input per row of the `reason` table in `SKILL.md`, plus the 2 MB boundary (2,097,152 bytes exactly and +1), a mixed array (exit 1), and a separator containing LF. Check exit code, stderr `reason`, and that no output file was written on exit 2.
4. **Python version.** Run the suite on 3.9 and the newest version you have. The skill claims 3.9+.

Spec gaps I found reading the code. Decide what's intended before you judge the results:
- **Row mode repeats scalars.** Scalar columns repeat on every expanded row. `SKILL.md` doesn't say so.
- **No `.csv` check.** Step 1 says the output should be a `.csv` name, but the script accepts any name.
- **Silent key collision.** A literal key `a.b` and nested `a` → `b` merge into one column. The docs call this a limit, not an error.

## Stage 2: trigger test (day 2)

Write 30 user prompts: 15 that should trigger the skill and 15 that shouldn't. Include CSV→JSON, "make an xlsx," a URL fetch, a top-level object, and a JSON-to-spreadsheet request phrased without the word "CSV." In arm B, check the transcript for skill invocation. Misfires mean the frontmatter `description` needs fixing, whatever the conversion results.

## Stage 3: task set

About 50 tasks. Each has a fixture and an oracle: an expected CSV, or an expected behavior. Hand-write the oracles for the small cases.

| Group | Count | Examples |
|---|---|---|
| A. Flat records | 5 | Key order varies across records; union of keys |
| B. Nested objects | 6 | Depth 4; empty `{}`; null inside nested; the fixture |
| C. Join arrays | 6 | Empty array; array of objects (compact JSON); `"; "` inside an item, with `--separator` |
| D. Row mode | 6 | Parallel arrays of unequal length; `items.name` columns; all arrays empty; no arrays |
| E. Value edges | 6 | `9.50`→`9.5`; `2**60`; emoji and RTL text; embedded newline and quotes; a leading `=` cell (should be written raw) |
| F. Stop / refuse | 8 | Top-level object; string; empty array; non-object-only array; output exists; output = input; 2.1 MB file; UTF-16; trailing comma; NaN |
| G. Scope | 5 | URL request; xlsx request; no output name given (should ask); CSV input (should not run the skill) |
| H. Messy real-world | 4 | `{"data":[...]}` wrapper (should ask, not unwrap); NDJSON; 80% blank column (must be named); BOM |

Write prompts in a few styles: terse, with a full path, and with no output name. Don't write them all the same way.

## Stage 4: runs

- **Pilot:** 10 tasks × 3 arms × 2 reps = 60 runs. Use it to check the harness and the oracles. Review every failure by hand; many early failures will be oracle bugs.
- **Full run:** 50 tasks × 3 arms × 3 reps = 450 runs. If cost is too high, drop to 2 reps. I haven't estimated tokens, so measure per-run cost in the pilot and multiply.
- **Per run:** fresh temp directory with a copy of the input, pinned model version, headless invocation, and capture of transcript, tool calls, exit codes, output file, input hash before and after, token counts and wall time.

## Stage 5: scoring

**Automatic, every run:**
- **Conversion tasks (A–E, H-conversion):** parse both files with Python's `csv` module. Pass only if the header list matches exactly and every row matches. Also record cell-level accuracy as a secondary metric.
- **Invariants:** input hash unchanged; nothing overwritten; no files written outside the run folder.
- **Disclosure:** on exit 1, every skipped index is named; on blank-heavy output, the worst three columns are named; output file name reported.
- **Stop/refuse tasks (F, G):** the expected action happened (stop, ask, or refuse), and no output file exists unless one should.

**Judged, only where the outcome needs it:** wording of stop/ask replies. Use a short rubric, graded blind, on a 20% sample.

**Report:** pass rate per arm per group, paired by task, with a bootstrap CI over tasks. Also report tokens, tool calls and time per task.

## Decision rules (write these down before the full run)

- **Keep** if the script passes Stage 1, and the skill arm beats baseline by at least 10 points overall with the CI excluding zero, or wins the guardrail groups (F, G, disclosure) without losing on conversion. Also keep if per-task tokens stay within 1.5× baseline.
- **Dead weight** if baseline is within 5 points of the skill on every group and the skill's wins aren't in the guardrail groups, or if the skill costs much more for no gain.
- **Split verdict:** if baseline already passes nearly all conversion tasks, the conversion value is zero and the decision rests on guardrails alone. The team then decides whether those are worth a skill file.
- **Rework first** if the script fails the oracle in a way that matters, or if the skill's refusals block cases the team wants handled, such as unwrapping `{"data":[...]}`. That second case is a product decision, not a test result.
- **Scope check:** if arm B misfires in Stage 2, fix the description and rerun Stage 2 before scoring.

Timing: Stage 1 on day 1, Stage 2 and the pilot on day 2, full run on days 3–4 (it can run overnight), analysis on day 5.

I can write the Stage 1 oracle and fuzz harness, or the task fixtures and checker, next. Say which you want first.
