# Web Dashboard

React + TypeScript analytics app (Vite, Tailwind, Zustand). Package manager: pnpm.

## Commands

- Install: `pnpm install`
- Dev server: `pnpm dev`
- Tests: `pnpm test` (vitest). Run before finishing; new code needs tests.
- Lint: `pnpm lint` (zero warnings allowed). Formatting and style (indentation, quotes, semicolons, no `var`, no `console`, no `any`) are enforced by `.prettierrc` and `.eslintrc.json`, so follow the tools rather than rules written here.
- Build: `pnpm build`

## Rules that are easy to get wrong

- NEVER edit `src/generated/`. Regenerate it with `pnpm gen:api` (source: OpenAPI spec).
- After changing `db/schema.sql`, run `pnpm db:migrate`, or the dev server crashes on start.
- Timestamps are stored in UTC. Display them only with `formatDate` from `src/lib/helpers.ts`. Never call `toLocaleString()` directly (it broke exports for US customers twice).
- Commit messages must be conventional commits: `type(scope): summary`. CI rejects anything else.
- Never commit secrets. Staging API keys come from the environment (`STAGING_API_KEY`); ask a teammate for the value.

## Layout

- `src/components/` components, `src/pages/` pages, `src/stores/` Zustand stores, `src/lib/` helpers.
- Styling uses Tailwind.
