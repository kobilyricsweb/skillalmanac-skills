# Audit of web-dashboard/CLAUDE.md

No agent skills were installed under `.claude/skills/`, so I audited directly against the repo files.

## What I found

**Wrong or stale facts (these actively misled the agent)**
- Said `npm install` / `npm run dev`; the project uses pnpm (`packageManager: pnpm@9.12.0`, `pnpm-lock.yaml`).
- Said `npm run test:unit`; no such script exists. The script is `test` (`pnpm test`).
- Said helpers live in `src/utils/helpers.ts`; the real file is `src/lib/helpers.ts`. The `formatDate` rule pointed at that file too, so it was undiscoverable.
- Referenced `legacy/admin/`; that directory does not exist.

**Contradiction**
- "Use tabs" and "Indent with 2 spaces" appeared together. `.prettierrc` says `useTabs: false`, `tabWidth: 2`, so spaces are correct.

**Security**
- A staging API key (`STAGING_API_KEY=stg_...`) was hardcoded in the file, which conflicts with the file's own "do not commit secrets" rule. It is removed from the file. Treat that key as exposed: rotate it, and check git history.

**Noise burying the real rules**
- Persona and pep-talk lines ("expert senior engineer", "do not make mistakes", "the user is counting on you"), the marketing project blurb, and a "General" section of vague reminders ("be careful", "quality matters", "think about performance"). These add no actionable information.
- Testing was stated five times; "IMPORTANT/ALWAYS/NEVER" emphasis was spread over generic items, so the few rules that matter (generated files, migrations, `formatDate`, commit format) lost their weight.
- About 15 style rules duplicate what ESLint/Prettier already enforce (const, no var, quotes, semicolons, no console, no any, unused imports). Generic advice like DRY/SOLID/"meaningful names" is unverifiable.

## What I changed

Replaced `web-dashboard/CLAUDE.md` (about 80 lines down to about 25) with:
- correct pnpm commands (install, dev, test, lint, build);
- a pointer to ESLint/Prettier as the source of truth for style, instead of restating it;
- only the five non-obvious, high-cost rules: never edit `src/generated/`, run `pnpm db:migrate` after schema changes, use `formatDate` from `src/lib/helpers.ts` (no `toLocaleString()`), conventional commit format, no secrets (key read from the environment);
- a short, corrected layout section.

No other files were modified.
