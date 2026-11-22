# Why the guard hook let a force-push through

Four problems in `infra-tools/.claude`, all fixed:

1. **Wrong input field.** `guard.js` read `tool_input.cmd`, but the Bash tool sends `tool_input.command`. `cmd` was always empty, so the regex never matched and nothing was ever blocked, from any directory. Fixed to read `command`.
2. **Wrong exit code.** The hook exited with 1, which Claude Code treats as a non-blocking error: the command still runs. Only exit code 2 blocks (stderr is shown to the agent). Fixed to exit 2 and write the message to stderr.
3. **Relative hook path.** `settings.json` ran `node .claude/hooks/guard.js`, which resolves against the current working directory. Inside `packages/api` the file does not exist, so node fails with a non-blocking error and the command runs. Fixed to `node "$CLAUDE_PROJECT_DIR/.claude/hooks/guard.js"`.
4. **Regex too narrow.** It only matched the literal `rm -rf` and `git push --force`. It missed `git push -f`, `--force-with-lease`, `git push origin +branch`, `rm -fr`, `rm -r -f` and `rm --recursive --force`. The patterns now cover these. A parse failure of the hook input now blocks instead of silently allowing.

Tested with sample inputs: all dangerous variants exit 2; `git push origin main`, `ls -la` and `rm file.txt` exit 0.
