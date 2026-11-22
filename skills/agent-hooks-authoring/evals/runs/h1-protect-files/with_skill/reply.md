# Reply

Hook: PreToolUse / `Edit|Write|MultiEdit|NotebookEdit` -> `shop-api/.claude/hooks/protect-files.js`
Installed in: `shop-api/.claude/settings.json` (existing permissions and Notification hook kept: yes). Timeout 10 seconds.
Fires when: the agent tries to edit a path that is `.env` or `.env.*`, anywhere under a `migrations/` directory, or `package-lock.json`. It exits 2 with a reason, so the edit is not made.
Fail mode: closed, because it is a guard; unreadable input or a missing path blocks.
Cross-platform: plain Node script (the project already requires Node 20+), no jq or python. The command uses `"$CLAUDE_PROJECT_DIR"` in quotes, so it works in macOS, Linux and Git Bash. Backslash and `..` paths are normalised, matching is by path segment and case-insensitive.
Choice to confirm: `.env.example`, `.env.sample` and `.env.template` are allowed (they are committed templates); `.env.production` and the like are blocked. `docs/migrations-guide.md` is allowed.

Tested (all fired with sample payloads):
- Blocked (exit 2): `.env`, `.env.production`, `.ENV`, `migrations/001_init.sql`, `migrations/sub/002.sql`, `package-lock.json`, `src/../.env`, relative `migrations/x.sql`, backslash path `src\..\.env`, Windows-style absolute path into migrations, run from `src/` with `../.env`.
- Allowed (exit 0): `docs/migrations-guide.md`, `src/app.js`, `.env.example`, `src/my routes.js`, a path outside the project.
- Empty, malformed JSON and missing path: exit 2 (fail closed).
- Config lint: 0 errors, 0 warnings.
- Not run: macOS and Linux themselves (only Git Bash on Windows was available).

Not covered: shell commands that write these files (`echo > .env`, `sed -i`, `npm install` rewriting package-lock.json), and scripts run by the agent. A Bash command guard can be added if you want that. Pattern guards reduce accidents; they are not a security boundary.
Turn off: remove the `PreToolUse` entry in `shop-api/.claude/settings.json`.
