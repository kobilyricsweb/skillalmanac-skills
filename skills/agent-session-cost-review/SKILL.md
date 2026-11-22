---
name: agent-session-cost-review
description: Finds where a coding-agent session spent its tokens, by parsing the saved session transcript (JSONL or a plain marker log) with a script that reports spend by phase, by tool and by costliest turn, plus repeated file reads, failing-command loops and oversized tool outputs, each with a line number, a token estimate and one fix. Use when the user hits a usage limit, asks where the tokens went, why a session cost so much, or wants to review a session's cost after the fact. Do not use to shorten replies going forward, to write a session handoff, or to read billing or invoice data.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual pass in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Agent session cost review

Measure after the fact where a session's budget went, name the exact lines, and attach one fix to each finding. This is a measurement job: report what the transcript shows, do not guess about turns that are not in it.

## Workflow

```
- [ ] 1 Find the transcript
- [ ] 2 Run the script
- [ ] 3 Check the data quality block
- [ ] 4 Read the ranked findings against the decision table
- [ ] 5 Apply one fix per finding
- [ ] 6 Report
```

1. **Find the transcript.** Ask the user which session, or take the newest. Agent tools save sessions as JSONL files under a per-project folder inside their config directory; search the home config folder for `*.jsonl` sorted by modified time if the user does not know. A directory argument is accepted: the script reads its newest 20 `.jsonl` files. If the session exists only on screen, ask the user to export it, or to paste it into a file using the marker format in [references/formats-and-thresholds.md](references/formats-and-thresholds.md). Never upload the transcript anywhere.
2. **Run the script** (run it, do not edit it):

```bash
python scripts/review_session.py <transcript.jsonl>
python scripts/review_session.py <transcript.jsonl> --oversized-chars 10000   # tighter threshold
```

   Output is one JSON document: `totals`, `by_phase[]`, `by_tool[]`, `top_turns[]`, `findings[]`, `savings[]`, `checks`, `notes[]`. Message bodies are cut to 80 characters and key-like strings are replaced by `[REDACTED]`. Do not quote more of the transcript than the script printed unless the user asks.
3. **Check `checks` first.** `unparseable_share` above 0.2 makes the script exit 1: say the numbers are unreliable and list `unparseable_samples`. `missing_timestamps` equal to every event means no time analysis is possible. `mixed_sessions: true` means the files are different sessions; review them separately. `totals.token_basis` says whether counts are estimates (4 ASCII characters per token) or partly from usage records; report it as given.
4. **Read `findings[]` in rank order** and map each `kind` with the table. Without Python: scan the transcript for the same shapes (a result you scrolled past that was pages long, the same file or command appearing three times) and treat the figures as unmeasured.

| `kind` | Rule that raises it | Fix to apply |
|---|---|---|
| `failing_loop` | Same call 3 or more times, 2 or more results look like errors | Stop re-running. Read the error once, state a hypothesis, change something, or ask the user |
| `repeated_command` | Same call 3 or more times, results not failing | Run once; keep the answer in the plan or a notes file |
| `repeated_read` | Identical read of one file 3 or more times with no edit to it in between | Restate the needed facts in the plan after the first read, or read a narrow range |
| `oversized_output` | Result over 20,000 characters and fewer than 3 of its long identifiers appear in later turns | Narrow the command (head, grep, range, summary flag); add an ignore rule for generated and vendor paths |
| `unused_context` | Result of 8,000+ characters in the first half of the session, 20+ events after it, not cited | Avoid early broad listings; for long sessions start fresh with a short handoff |
| `whole_file_read` | Read with no range returning over 12,000 characters | Search for the symbol, then read the range around it |
| `verbose_reply` | One assistant text block over 1,000 tokens | Lead with the change; drop recaps; ask for short answers |

5. **Apply one fix per finding**, highest `estimated_saving_tokens` first. The fix is a change in how the user prompts or configures the agent (an ignore rule, a narrower command, a standing instruction, a fresh session), so write it as text the user can paste. Do not apply config changes without being asked.
6. **Report** in this fixed shape, at most 15 lines:

```
Session: <file>, <events> events, ~<estimated_tokens> tokens (<token_basis>)
Where it went: <top 3 phases with share_pct>, top tool <name> <share_pct>
Findings: <rank>. <kind> at line <evidence_line>, ~<estimated_tokens> tokens -> <one-line fix>
Possible saving: ~<totals.estimated_saving_tokens> tokens (<share>% of this session)
Data quality: <unparseable lines, missing timestamps, mixed sessions, basis>
Not measured: <what the transcript cannot show, see Limits>
```

## Reading the numbers

- `by_phase`: `explore` (reads, searches, listings), `edit`, `run` (shell), `other` tools, `reply` (assistant text and thinking), `prompt` (user and system text). A result belongs to the phase of the call that produced it. Explore above 60% with no findings usually means the task needed broad reading; the remedy is a better first prompt naming the files.
- `savings[]` counts each event once, in the first rule that claims it (loops, then repeated reads, then oversized, whole-file, unused context, verbose). The saving is `estimated_tokens` times a factor (0.5 to 1.0) because a narrowed read still returns something.
- Totals are the sum of single events. They do not include the cost of re-sending earlier context on every turn, which is why real usage is far higher than the estimate; see Limits.

## Scripts

- `scripts/review_session.py <paths> [flags]`: run it. Flags `--oversized-chars`, `--whole-file-chars`, `--unused-context-chars`, `--unused-context-min-following`, `--loop-min`, `--verbose-tokens` change the thresholds above; report any non-default value you used. Exit 0 report produced, 1 report produced but over 20% of lines unparseable, 2 no usable input. It reads only the paths given and prints JSON; it never writes, uploads or runs anything from the transcript.

Never edit the script to make a finding disappear.

## Limits

- Token figures are estimates (or usage counts split by characters), not billing. Cached input, system prompts and hidden reasoning that the export omits are not counted.
- The script sums what each turn added; the true cost of a large early result includes being re-sent with every later turn. A finding's estimate is therefore a floor.
- "Cited later" is a vocabulary overlap test on identifiers of 10 or more characters. A result used only by eye, or only through short names, can be flagged as unused; read the evidence line before deleting a habit.
- Tool names are matched against common spellings. An unknown tool is classed `other` and cannot be flagged as a read or a loop of reads; shell commands are classed by the first program word.
- Repeated streamed records of one message are deduplicated by message id; exports without ids can overcount usage.
- Transcripts may hold secrets and personal data. Redaction covers common key shapes only; do not paste raw transcript lines into other tools.
- Thresholds are working values, not measured optima.
