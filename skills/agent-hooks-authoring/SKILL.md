---
name: agent-hooks-authoring
description: Writes, installs, tests and debugs coding-agent hooks, the commands a harness runs automatically before or after tool calls, on prompt submit, at session start or when the agent tries to stop. Use when the user asks for a hook, wants something to happen every time (format after each edit, block rm -rf or force-push, protect .env or migrations, keep going until tests pass, inject context), or says a hook is not firing or blocks everything. Do not use for git hooks (pre-commit, husky), React hooks, webhooks, or plain permission allow/deny rules.
license: Apache-2.0
compatibility: Event names, file locations and the lint script target Claude Code hooks (the hooks block in .claude/settings.json). The design and testing rules carry to other harnesses with hooks, the reference tables do not. The lint script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Agent hooks authoring

A hook is code that runs with the user's full permissions, on every matching event, without anyone reading its output. A hook that was never fired with real input is a guess. The job is finished only when the hook has been fired with sample input for the block case, the allow case and the awkward cases, and the results are shown.

## Workflow

### 1. Confirm a hook is the right tool

| The user wants | Use |
|---|---|
| Something to happen every time, whatever the model decides | a hook |
| A tool or path never to be used at all | a permission deny rule is simpler; offer it, add a hook only for logic a rule cannot express |
| Guidance the model should weigh | an instruction file, not a hook |

### 2. Pick the event, the matcher and the file

Read [references/events-and-io.md](references/events-and-io.md) for the event table, the input fields, and what each exit code does on that event. Do not rely on memory for these: the three facts that break most hooks are in that file (which events can block, which field carries the data, what unit the timeout uses).

- Shared with the team: `.claude/settings.json`. Personal: `.claude/settings.local.json` or `~/.claude/settings.json`.
- **Merge, never overwrite.** Read the existing settings file first and add to the `hooks` object. Leave every other key and every existing hook as it was.

### 3. Write the handler as a script file

Put logic in `.claude/hooks/<name>.<ext>`, not in a one-line shell string. Then:

1. **Runtime**: use an interpreter the project already requires (a Node project gets a Node script). Check that it is on the PATH. Do not assume `jq` or `python3` exist; on Windows `python3` is often a stub.
2. **Path to the script**: `"$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>` with the variable inside double quotes. A relative path breaks as soon as the agent changes directory.
3. **Input**: read all of stdin, parse the JSON, take fields by their exact names from the reference.
4. **Blocking**: exit code 2 with the reason on stderr. Exit 1 is reported as an error and blocks nothing.
5. **Failure mode**: decide what happens when the input cannot be parsed or a field is missing. A security guard fails closed (exit 2). A convenience hook (formatting, notifications) fails open (exit 0). Say which was chosen.
6. **Paths in input**: normalise backslashes to forward slashes, resolve `..`, compare against the project root, and match on path segments. Substring tests are wrong in both directions (`docs/migrations-guide.md` is not in `migrations/`; `src/../.env` is `.env`).
7. **Commands in input**: split compound commands on `&&`, `||`, `;` and `|`, then match tokens. Flags come in several spellings and positions (`--force`, `-f`, after the branch name; `-rf`, `-fr`, `-r -f`). A flag only counts when it belongs to the command being guarded (`grep -rf` is not `rm -rf`).
8. **Stop and SubagentStop hooks**: read `stop_hook_active`. When it is true the agent is already continuing because of this hook; either allow the stop or keep a bounded retry count. State in the report which one and why.
9. **Speed and timeout**: the timeout is in seconds. Set one that fits the work (a test run needs more than a path check) and keep pre-tool hooks well under a second.
10. **Arguments to child commands**: pass file paths as separate arguments, never spliced into a shell string, so spaces and quotes survive.

Skeletons for the common jobs are in [references/recipes.md](references/recipes.md); read the one that matches.

### 4. Fire it before saying it works

Copy a payload from `assets/payloads/` (`pre-tool-edit.json`, `pre-tool-bash.json`, `post-tool-write.json`, `stop.json`, `user-prompt-submit.json`, `session-start.json`), edit the fields, and pipe it in exactly as the harness would:

```bash
CLAUDE_PROJECT_DIR="$PWD" node .claude/hooks/guard.js < payload.json; echo "exit=$?"
```

Minimum cases; record the exit code of each:

| Case | Expect |
|---|---|
| the thing that must be blocked, in its plain form | exit 2 and a reason on stderr |
| each variant spelling or path form from step 3 (6 and 7) | exit 2 |
| two ordinary inputs that look similar but must pass | exit 0 |
| run from a subdirectory of the project | same results |
| empty or malformed stdin | the failure mode chosen in step 3 |
| for a Stop hook: failing state, passing state, and `stop_hook_active: true` | block, allow, and the documented choice |

If a case cannot be run (interpreter missing in this environment), say so in the report; do not describe it as tested.

### 5. Lint the configuration

```bash
python scripts/hook_config_lint.py path/to/.claude/settings.json
```

Run the script; do not edit it to make a finding go away. Fix each `ERROR`. Read each `WARN` and either fix it or explain it in the report. It catches unknown event names, a handler placed one level too high, timeouts that look like milliseconds, relative or unquoted script paths, matchers that match nothing, Stop hooks with no loop guard, and guards that exit 1. Without Python, check the same list by hand against the reference.

### 6. Report

```
Hook: <event> / <matcher> -> <script path>
Installed in: <settings file>   (existing keys and hooks kept: yes/no)
Fires when: <one line>
Fail mode: <closed|open> because <reason>
Tested: <table of case -> exit code>
Not covered: <ways around it, cases not run>
Turn off: <which entry to remove>
```

"Not covered" is never empty for a guard. A hook on file-editing tools does not see shell commands that write files; a hook on shell commands does not see scripts the command runs. Say which gaps remain and offer the second hook when the user asked for protection rather than convenience.

## Debugging a hook that misbehaves

Work in this order and stop at the first cause, then keep checking the rest, because broken hooks usually have more than one defect:

1. Is the event name spelled exactly, and is the handler inside `hooks: [...]` of a matcher group?
2. Does the matcher equal the tool name exactly (tool names are capitalised)?
3. Does the script path resolve from another working directory?
4. Fire it by hand with a real payload. Does it read the right field? What is the exit code?
5. Is the reason on stderr, and is the exit code 2?
6. Is the timeout a sensible number of seconds?
7. Are the patterns wide enough for the variants in step 3?

Report every defect found, not only the first.

## Limits

- Facts in the reference describe one harness and change between releases; when behaviour disagrees with the reference, check the harness documentation and say so.
- A hook cannot undo a tool call that has already run; post-tool hooks only add feedback.
- Pattern-based guards reduce accidents. They do not stop a determined bypass and are not a security boundary.
- The lint script reads configuration and, when it can find them, the script files; it does not execute hooks.
