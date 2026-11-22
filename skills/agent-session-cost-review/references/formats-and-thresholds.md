## Contents

- Accepted layouts
- Marker log format
- Token estimate
- Event classification
- Why these thresholds
- Output fields

## Accepted layouts

The script detects each file by itself and reports the choice in `files[].format`.

| Format | What it looks like | Notes |
|---|---|---|
| `jsonl` | One JSON object per line | Blank lines are skipped; lines that are not JSON are counted in `invalid_json_lines` |
| `json_document` | A JSON list of records, or an object with a `messages` list | `evidence_line` is then the entry number, starting at 1 |
| `marker_log` | Plain text with marker lines (below) | First non-blank line must be a marker |

Record shapes understood inside JSON formats:

- `role` plus `content`, where content is a string or a list of blocks of type `text`, `input_text`, `output_text`, `thinking`, `tool_use` (id, name, input) and `tool_result` (tool_use_id, content, is_error).
- The same inside a `message` object, with the outer record carrying `timestamp` and `sessionId`.
- Chat-style: an assistant record with `tool_calls` (id, function.name, function.arguments as a JSON string) answered by `role: tool` records with `tool_call_id`.
- Standalone records of type `function_call` and `function_call_output` (call_id).
- Roles `developer` and `system` are counted as system text.

A record with no recognisable role (summaries, snapshots, queue markers) is counted in `unrecognized_records`, not silently dropped. Both counts add up to `checks.unparseable_total`.

## Marker log format

Each marker starts a line with three hash signs. Text after a marker, up to the next marker, belongs to it.

```
### user
Free text of the user message.
### assistant
Free text of the assistant message.
### tool_call Bash: pytest tests/test_cart.py
### tool_result
Output text of the previous call.
### tool_call Read: src/cart.py lines 10-40
```

For a shell-type tool the text after the colon is the command. For read, edit and search tools the first word is the path; the words `lines`, `offset` or `limit` anywhere in the argument mark the read as ranged. A result pairs with the earliest unanswered call. Text before the first marker is counted as unparseable.

## Token estimate

Each event is estimated at ceil(ASCII characters / 4 + other characters / 2). Four characters per token is the usual rough figure for English prose and source code; non-ASCII text (many scripts, emoji) packs worse, so it is counted at two. When an assistant record carries `usage.output_tokens`, that number is shared among the record's assistant and tool-call events in proportion to characters, and `totals.token_basis` says so. Input-side usage is summed into `totals.reported_usage` for comparison but is not attributed to turns, because it includes the repeated context.

Use the estimate to rank, not to bill. Two sessions compared on the same heuristic are comparable; the estimate against an invoice is not.

## Event classification

A tool call is classed `read`, `search`, `edit`, `run` or `other`:

- By tool name: names such as Read, read_file, view are reads; Edit, Write, apply_patch, str_replace are edits; Grep, Glob, find, list_dir are searches; Bash, shell, powershell, exec_command are shells.
- Shell commands are classed by the first program of the line: cat, type, head, tail, get-content, bat, less, sed -n are reads (head, tail, sed and any piped read count as ranged); grep, rg, find, ls, dir, tree, fd and git log/diff/show/status/grep are searches; sed -i, tee and output redirection are edits; everything else is `run`.
- Phase: read and search map to `explore`, edit to `edit`, run to `run`, other to `other`.

A result inherits tool, target, op and phase from its call. A result is `failing` when it contains a traceback, FAILED, ERROR, "Error:", a non-zero exit code, "command not found", "No such file", "npm ERR!" or "Permission denied", or the record sets is_error.

## Why these thresholds

| Constant | Value | Reason |
|---|---|---|
| Oversized result | 20,000 characters | About 5,000 tokens; larger than what a single next step usually needs, so it is almost always better narrowed |
| Whole-file read | 12,000 characters | About 3,000 tokens; above this a range read almost always carries what the next step needs |
| Unused context | 8,000 characters, first half, 20 events after | Big early results are re-sent on every later turn, so the cost multiplies with the tail length |
| Loop | 3 identical calls | Two is a retry; three is a pattern |
| Repeated read | 3 identical reads, edits excluded | Re-reading after an edit is correct; re-reading an unchanged file is memory loss |
| Verbose reply | 1,000 tokens in one text block | Long enough to be an essay, short enough to catch recaps |
| Cited | 3 shared identifiers of 10+ characters | One shared long word can be a coincidence; three is a reference |
| Parse failure | 20% of non-blank lines | Beyond this the picture is more guess than measurement |

Overridable with flags: oversized, whole-file, unused context (both values), loop, verbose reply. Repeated-read count, the citation test and the parse-failure share are fixed in the script.

## Output fields

`findings[]`: `rank`, `kind`, `file`, `evidence_line` (first line), `evidence_lines` (up to 10), `tool`, `estimated_tokens`, `estimated_saving_tokens`, `detail`, `evidence` (80-character redacted preview), `remedy`. `savings[]` sums the findings per kind with `share_of_total_pct`. `top_turns[]` lists the 10 largest single events. `by_tool[]` gives calls, call tokens, result tokens and the largest result in characters per tool name.
