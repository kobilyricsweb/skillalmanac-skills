# crm-web rules migration

All new files are under `crm-web/`. Nothing old was deleted.

| Source | Activation there | Destination | Why | Changed or dropped |
|---|---|---|---|---|
| `.cursor/rules/core.mdc` | always | `AGENTS.md` | short, applies to all work | kept all 5 rules; added reason for pnpm (package.json pins pnpm@9.12.0) |
| `.cursorrules` | always (legacy) | `AGENTS.md` | same content as core.mdc plus one extra rule | 3 lines were duplicates (pnpm, zod, default exports), merged; unique rule `toastError`, never `alert()` kept |
| `.cursor/rules/hotfix.mdc` | always (misplaced: 17 lines, 7 steps) | skill `hotfix-release` + one-line pointer in `AGENTS.md` | long procedure loaded every session | nothing dropped; the 3 "do not" rules, 3 checks and 7 steps kept, check list moved to the end. Pointer also keeps "never merge release into main" always visible |
| `.cursor/rules/release-process.mdc` | model decision | skill `cutting-a-release` | procedure | nothing dropped; Friday-14:00 rule kept; added closing check |
| `.cursor/rules/db-migration.mdc` | model decision | skill `writing-prisma-migrations` | procedure | nothing dropped |
| `.cursor/rules/react-components.mdc` | glob `src/components/**/*.tsx` | `src/components/AGENTS.md` | file-pattern convention | nothing dropped |
| `.cursor/rules/scratch.mdc` | manual, no description | skill `investigating-react-performance` | checklist; a description was written (it had none) | reordered into a workflow (network check before why-did-you-render); no fact lost |

Also created `CLAUDE.md` containing only `@AGENTS.md` so Claude Code reads the shared file. Codex and Cursor read `AGENTS.md` directly.

Skills are written in `crm-web/.agents/skills/<name>/` (source copy) and `crm-web/.claude/skills/<name>/` (identical copy for Claude Code). Keep the two identical; verified with `diff -r`.

## Conflicts
None. `core.mdc` and `.cursorrules` agree; pnpm is confirmed by `packageManager` in package.json.

## Things the repo does not back up (not changed, please check)
- `prisma` is not in package.json scripts or dependencies, so `pnpm prisma ...` assumes it is installed.
- `src/components/Button.tsx` has no `Button.stories.tsx`, so the stories rule is already violated.
- No `useFlag` hook, `toastError`, `CHANGELOG.md`, `docs/incidents/` or `tools/notes.mjs` exist in this checkout (may live elsewhere); `src/schemas/contact.ts` is a stub, not a zod schema.

## Lost or weakened
- Glob precision: `src/components/AGENTS.md` covers the directory, not `*.tsx` only. Cursor users still have the old glob rule while it exists.
- Manual attach (scratch): the skill can now also trigger by itself from its description.
- `hotfix` was always-on and is now on-demand; only the pointer is always loaded.

## Old files
Kept. Cursor reads both `.cursor/rules` and `AGENTS.md`, so its users now load the core rules twice and may see duplicate hotfix text. Recommended: once the team confirms the new setup, delete `.cursorrules` and `.cursor/rules/*.mdc` (Cursor also reads `AGENTS.md` and `.claude/skills`). Until then edits must be made in both places or they will drift.
Cursor's `/migrate-to-skills` would only convert the model-decision rules; it skips always-on and glob rules, which were handled by hand here.

## Check in each tool
Ask each of Claude Code, Codex and Cursor: "Which instruction files and skills did you load?" Expect AGENTS.md (and CLAUDE.md for Claude Code) plus the four skills; in `src/components` also the nested AGENTS.md.
