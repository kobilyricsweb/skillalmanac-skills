# Why the force-push got through

Defects found in `infra-tools/.claude/` (all fixed):

1. **Wrong input field.** The guard read `tool_input.cmd`; Claude Code's Bash payload field is `tool_input.command`. The command was always empty, so nothing ever matched.
2. **Wrong exit code.** It blocked with `exit(1)`. Only exit 2 blocks a PreToolUse call; exit 1 is a non-blocking error, so the command ran anyway. The reason also went to stdout instead of stderr.
3. **Relative hook path.** `node .claude/hooks/guard.js` resolves against the current directory. Once the agent was inside `packages/api` the script was not found (node exits 1, non-blocking), so the hook silently did nothing. Now `node "$CLAUDE_PROJECT_DIR"/.claude/hooks/guard.js`.
4. **Timeout in milliseconds.** `"timeout": 5000` is seconds (about 83 minutes). Now `5`.
5. **Fails open.** `JSON.parse` was unguarded, so bad input crashed with exit 1 (allow). Now unreadable input exits 2 (fail closed).
6. **Patterns too narrow.** `/rm -rf|git push --force/` missed `git push -f`, `git push origin main --force`, `rm -fr`, `rm -r -f`, `+branch` refspecs, and compound commands. Now commands are split on `&&`, `||`, `;`, `|`, tokenised, and `sudo`/`env`/`VAR=x` prefixes are stripped. `--force-with-lease`, `grep -rf` and plain `git push`/`rm file` are allowed.

Possible additional cause (not verifiable here): the hook lives in `infra-tools/.claude/settings.json`. If the agent session was started from `packages/api` or the repo root rather than `infra-tools`, Claude Code would not load that file at all. Start sessions from `infra-tools`, or move the hook to the real project root.

Tested (exit codes): `git push --force`, `-f`, trailing `--force`, `cd a && git push -f`, `rm -rf`, `rm -fr`, `rm -r -f`, `+main`, `sudo rm -rf` all 2; `git push`, `rm file`, `grep -rf`, `--force-with-lease` all 0; malformed stdin 2; run from `packages/api` with the absolute script path 2. Config lint: 0 errors, 0 warnings.

Not covered: commands wrapped in `sh -c "..."`, aliases, scripts that run these commands internally, and any non-Bash tool. Pattern guards reduce accidents; they are not a security boundary.
