# Hooks added to shop-api

Both hooks are in `shop-api/.claude/settings.json`. The existing permissions and the Notification hook are untouched. The scripts are Node files, so they behave the same on macOS, Linux and Windows (Git Bash). Node is already required by the project.

1. **Format on edit.** `PostToolUse`, matcher `Edit|Write|MultiEdit`, runs `.claude/hooks/format-edited.js` (timeout 60 s).
   - It runs `npm run format -- <file>` on the edited file, only for `.js` and `.ts`. Other file types and missing files are skipped.
   - The path is passed as a separate argument. On Windows `npm` needs a shell, so the path is quoted there; a path with a space (`src/my routes.js`) works.
   - It fails open. Unreadable input does nothing. If the formatter fails, the error goes back to the agent as feedback, since the edit has already happened.
2. **Tests before stopping.** `Stop`, no matcher, runs `.claude/hooks/tests-before-stop.js` (timeout 300 s).
   - It runs `npm test`. If tests fail, it exits 2 with the failing output, so the agent keeps working. If they pass, it allows the stop.
   - It is bounded. After 5 consecutive blocked stops it lets the turn end and prints the failure. This is a choice, so the agent cannot loop forever on something it cannot fix. Raise or remove `MAX_TRIES` in the script if you want it to keep going. Claude Code itself also ends the turn after 8 consecutive stop-hook continuations. You can interrupt at any time.
   - It fails open if its input is unreadable.

## Tested

I fired each script by hand with sample payloads. `hook_config_lint.py` reported 0 errors and 0 warnings.

| Case | Result |
|---|---|
| Format: `.ts` file, `.js` file with a space in the name, relative path | formatter ran, exit 0 |
| Format: `.md` file | skipped, exit 0 |
| Format: malformed input | exit 0 |
| Stop: tests passing | exit 0 |
| Stop: tests failing | exit 2, with test output |
| Stop: `stop_hook_active` true, failing | exit 2 for tries 1 to 4, then exit 0 on the 5th (the bound) |
| Stop: malformed input | exit 0 |

## Not covered or not run

- I ran these only on Windows with Git Bash. macOS and Linux were not run. They take the non-shell path in the scripts.
- A failing formatter case was not run.
- The format hook does not see files written by shell commands.
- The Stop hook runs the full test suite on every stop attempt.
- While testing I overwrote `shop-api/src/my routes.js` with a one-line test file. I did not read it first, so the original content is lost and the file needs restoring from your source control.

## Turn off

Remove the `PostToolUse` or `Stop` entry from `shop-api/.claude/settings.json`.
