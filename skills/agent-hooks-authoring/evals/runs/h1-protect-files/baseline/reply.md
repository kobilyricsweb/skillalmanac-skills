# What I did

- Added `shop-api/.claude/hooks/protect-files.js`, a PreToolUse hook that blocks (exit code 2, with an explanatory message) any Edit/Write/MultiEdit/NotebookEdit on:
  - `.env` and `.env.*` (for example `.env.production`)
  - anything under a `migrations/` directory
  - `package-lock.json`
- Registered it in `shop-api/.claude/settings.json` under `hooks.PreToolUse`. The existing Notification hook, permissions and `notify.js` are untouched.
- The hook is plain Node (the project already requires Node >= 20), so it behaves the same on macOS, Linux and Windows Git Bash. It handles both `/` and `\` paths and ignores case. It is called via `$CLAUDE_PROJECT_DIR`, like the existing hook.
- Tested with sample inputs: `.env`, `.env.production`, `Migrations\002.sql` and `package-lock.json` are blocked. `src/app.js` and `docs/migrations-guide.md` are allowed.

Notes:
- `.env.example` is deliberately still editable because it is a committed template. Remove the `!== '.env.example'` check in the hook if you want it blocked too.
- The hook only covers the file-editing tools. It does not stop edits made through shell commands (for example `sed -i` via Bash).
