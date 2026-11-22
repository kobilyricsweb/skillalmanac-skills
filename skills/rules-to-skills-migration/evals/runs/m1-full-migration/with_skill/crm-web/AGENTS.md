# crm-web

Next.js CRM front end. Shared by Cursor, Claude Code and Codex users.

## Rules that always hold

- Package manager is pnpm (`packageManager` in package.json is pnpm@9.12.0). Never run npm or yarn, because they would create a second lockfile.
- Request and form validation uses zod schemas in `src/schemas/`. Do not validate by hand.
- Feature flags are read with the `useFlag` hook. Never read `window.__FLAGS__` directly.
- No default exports, except Next.js pages.
- Show API errors to the user with `toastError`, never `alert()`.
- Run `pnpm typecheck` and `pnpm test` before saying a change is done.

## Procedures (skills)

- Production is broken and the fix cannot wait: use the `hotfix-release` skill. Never merge `release` into `main`.
- Regular release: `cutting-a-release`. Prisma schema change: `writing-prisma-migrations`. Slow UI: `investigating-react-performance`.

Component conventions are in `src/components/AGENTS.md`.
