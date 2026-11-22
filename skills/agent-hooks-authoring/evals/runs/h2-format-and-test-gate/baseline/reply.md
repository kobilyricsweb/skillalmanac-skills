# Hooks added to shop-api

Both hooks are in `shop-api/.claude/settings.json`. The existing Notification hook and permissions are unchanged.

1. **Format on edit** (`PostToolUse`, matcher `Edit|Write|MultiEdit`): `.claude/hooks/format-file.js` reads the edited path from the hook input. For `.js` and `.ts` files only, it runs `npm run format -- "<file>"` on that one file. Paths with spaces (such as `src/my routes.js`) work.
2. **Tests must pass to stop** (`Stop`): `.claude/hooks/require-tests.js` runs `npm test`. If it fails, the hook exits 2 and sends the failure output back, so the agent keeps working. If tests pass, the agent can finish.

Both hooks are small Node scripts, so there is no dependency on `jq` or bash and they behave the same on macOS, Linux and Windows (Git Bash). Node is already required (>=20).

I checked the format hook and the Stop hook by running them by hand. The formatter ran on a path with a space, and the Stop hook returned exit 0 with tests passing.

Caveat: if the agent cannot fix a failing test, the Stop hook will keep blocking it. Interrupt the session manually if that happens.
