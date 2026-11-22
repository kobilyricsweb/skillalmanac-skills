# Hook events, input and output (Claude Code)

## Contents

- Configuration shape
- Where hooks can live
- Events most hooks use
- Matchers
- Input on stdin
- Exit codes
- JSON output
- Stop hooks and loops
- Timeouts
- Environment
- Security notes
- Sources

## Configuration shape

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/guard.js", "timeout": 10 }
        ]
      }
    ]
  }
}
```

Three levels: event name, then a list of matcher groups, then each group's `hooks` list of handlers. A handler placed directly in the group (next to `matcher`) is not run.

Handler types: `command` (shell command; fields `command`, optional `args` for exec form without a shell, `timeout`, `shell`), `http`, `mcp_tool`, `prompt`, `agent`. Use `command` unless the user asks otherwise.

## Where hooks can live

| File | Scope |
|---|---|
| `~/.claude/settings.json` | every project of this user |
| `.claude/settings.json` | this project, committed |
| `.claude/settings.local.json` | this project, not committed |
| managed policy settings | organisation |
| plugin `hooks/hooks.json`, skill or subagent frontmatter | while that component is active |

Entries from all levels are merged. The `/hooks` command lists what is loaded and from which file.

## Events most hooks use

| Event | Fires | Matcher filters on | Can exit 2 block? |
|---|---|---|---|
| `PreToolUse` | before a tool call | tool name | yes, the call is not made |
| `PostToolUse` | after a tool call succeeded | tool name | no; stderr is shown to the model as feedback |
| `UserPromptSubmit` | when the user sends a prompt | none | yes, the prompt is rejected |
| `Stop` | when the agent is about to end its turn | none | yes, the agent continues |
| `SubagentStop` | when a subagent is about to finish | agent type | yes |
| `SessionStart` | session start or resume | source: `startup`, `resume`, `clear`, `compact` | no |
| `PreCompact` | before compaction | `manual`, `auto` | yes |
| `Notification` | the harness notifies the user | notification type, for example `permission_prompt`, `idle_prompt` | no |
| `SessionEnd` | session ends | reason | no |

Other events exist (permission requests, task events, file and directory changes, model switches). Check the harness documentation before using one that is not in this table.

## Matchers

- Omitted, `""` or `"*"`: matches everything.
- Only letters, digits, `_`, `-`, spaces, commas and `|`: an exact name or a list of exact names (`Edit|Write`).
- Anything else: an unanchored regular expression (`mcp__memory__.*`). Anchor with `^...$` for a full match.
- Tool names are capitalised: `Bash`, `Edit`, `Write`, `Read`. MCP tools are `mcp__<server>__<tool>`; a bare `mcp__server` matches nothing.
- A matcher on an event that takes none is ignored.
- File-editing tools: match at least `Edit|Write`; add `MultiEdit|NotebookEdit` when notebooks or multi-edits matter.

## Input on stdin

One JSON object. Common fields: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`.

| Event | Extra fields |
|---|---|
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id` |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response`, `tool_use_id` |
| `UserPromptSubmit` | `prompt` |
| `Stop` | `stop_hook_active`, `last_assistant_message` |
| `SubagentStop` | `stop_hook_active`, `agent_id`, `agent_type`, `agent_transcript_path` |
| `SessionStart` | `source` |
| `PreCompact` | `trigger`, `custom_instructions` |
| `Notification` | `message`, `notification_type` |

`tool_input` by tool: `Bash` has `command`; `Edit` has `file_path`, `old_string`, `new_string`; `Write` has `file_path`, `content`; `Read` has `file_path`. File paths are normally absolute and on Windows may contain backslashes.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success. If stdout is a single JSON object it is parsed (see below). Plain stdout becomes context on `UserPromptSubmit` and `SessionStart`; elsewhere it is not shown to the model |
| 2 | Blocking error on events that can block; stderr is the reason given to the model. On events that cannot block, stderr is only shown |
| any other | Non-blocking error. The action proceeds. This includes exit 1 |

## JSON output

Printed on stdout with exit code 0.

- Any event: `continue` (false stops the agent entirely), `stopReason`, `systemMessage`.
- `PreToolUse`: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny" | "allow" | "ask", "permissionDecisionReason": "..."}}`. `updatedInput` replaces the whole tool input. The older top-level `decision` of `approve` or `block` on this event is deprecated.
- `Stop`, `SubagentStop`, `PostToolUse`, `UserPromptSubmit`: `{"decision": "block", "reason": "..."}`.
- `UserPromptSubmit`, `SessionStart`, `PostToolUse`: `hookSpecificOutput.additionalContext` adds text to the model's context. Output added to context is capped at 10,000 characters.

Exit code 2 with stderr is the simplest way to block and is enough for most guards. Use JSON only when a field is needed.

## Stop hooks and loops

`stop_hook_active` is true when the agent is already continuing because a stop hook blocked. A hook that blocks whenever a condition is unmet will keep the agent going until the condition is met; the harness ends the turn anyway after 8 consecutive stop-hook continuations (the counter resets when the agent calls a tool). Do not rely on that cap as the design: decide what should happen when the agent cannot fix the problem, and tell the user how to interrupt.

Typical pattern: block when the check fails and include the failing output in the reason; when `stop_hook_active` is true and the check still fails after a bounded number of attempts (a counter file under the project's temporary directory, keyed by `session_id`), allow the stop and print the failure.

## Timeouts

`timeout` is in **seconds**. Default 600 for command handlers (30 on `UserPromptSubmit`). A value such as 5000 is 83 minutes, not 5 seconds. A hook that exceeds its timeout is cancelled and treated as a non-blocking error, so a guard that times out lets the action through.

## Environment

- `CLAUDE_PROJECT_DIR`: absolute project root. Use it for script paths, in double quotes. In PowerShell handlers use `$env:CLAUDE_PROJECT_DIR`.
- `CLAUDE_ENV_FILE`: only on `SessionStart` and a few related events; append `export NAME=value` lines to make variables available to later shell commands.
- Matching hooks for one event run in parallel; do not depend on order.

## Security notes

- Hooks run with the user's full permissions. Review a hook like any script that runs unattended.
- In interactive sessions hooks are held until the workspace is trusted. Non-interactive runs treat the folder as trusted, so committed hooks run there without a prompt.
- Quote every shell variable, reject `..` after resolving, and skip sensitive files rather than reading them.

## Sources

Hooks reference of the Claude Code documentation (code.claude.com/docs/en/hooks), read 2026-11-20. Facts not on that page were left out.
