# crm-web

Next.js CRM front end. Conventions below apply to every change.

- Package manager is pnpm. Never run npm or yarn here.
- Request and form validation uses zod schemas in `src/schemas/`. Do not validate by hand.
- Feature flags are read with the `useFlag` hook. Never read `window.__FLAGS__` directly.
- No default exports, except Next.js pages.
- API errors are shown to the user with `toastError`, never `alert()`.
- Run `pnpm typecheck` and `pnpm test` before saying a change is done.

Component conventions live in `src/components/AGENTS.md`. Step-by-step procedures are skills: `db-migration`, `release-process`, `hotfix`, `perf-investigation`.
