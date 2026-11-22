Files: web-dashboard/CLAUDE.md (83 lines -> 25)
Verified against: package.json, pnpm-lock.yaml, .prettierrc, .eslintrc.json, tools/*.mjs, db/schema.sql, src/generated/api.ts, src/lib/helpers.ts, src/stores/. No CI config or README in the workspace.

Why it was ignored: about 40 of 67 non-blank lines were generic ("be careful", "think about security", "Do not make mistakes"), plus a persona and marketing paragraph. The five rules that matter (generated code, migrate after schema change, UTC dates, commit format, test/run commands) were buried among them. Seven emphasis markers diluted each other. Two lines contradicted each other.

Fixed:
- `npm install` / `npm run dev` -> `pnpm install` / `pnpm dev` (lockfile and `packageManager: pnpm@9.12.0`).
- `npm run test:unit` does not exist -> `pnpm test` (package.json script `test`: vitest run). Also added `pnpm lint` and `pnpm build`, which exist in package.json.
- `src/utils/helpers.ts` does not exist -> `src/lib/helpers.ts` (contains `formatDate`).
- `legacy/admin/` does not exist in the repo -> removed and left a TODO(owner).

Conflicts settled:
- "Use tabs" vs "Indent with 2 spaces" -> 2 spaces, because .prettierrc has `useTabs: false, tabWidth: 2`. The style rules are now just a pointer to the prettier and eslint configs.

Removed:
- Persona and pep talk (3 lines), project history and marketing (6 lines), the "General" section (10 lines), vague testing and git lines (about 8), and style rules enforced by eslint or prettier (single quotes, semicolons, const, no var, no console, no any, unused imports).
- Generic advice such as DRY, SOLID, "keep functions small", "meaningful names".
- The duplicated "tests must pass" lines, collapsed into one command line.
- Directory listings that are obvious from the layout (components, pages, Tailwind).

Kept: the generated-code ban, the `db:migrate` ordering trap, the UTC and `formatDate` rule with its reason, the conventional-commit rule, the Zustand location, the real commands.

Needs the owner:
- SECRET: the file contained a staging API key (line 21, starts `stg_k3y_`). It is in version history, so rotate it. The file now says to read it from the `STAGING_API_KEY` environment variable.
- TODO: where the legacy admin panel lives, or whether it is gone.
- TODO: name and location of the OpenAPI spec (the generated header says `openapi.yaml`, but no such file is in the repo).
- Not verifiable here: the "CI rejects non-conventional commits" claim (no CI config present); kept as stated by the file.
- Observation, not changed: `formatDate` uses the `en-GB` locale, which may not suit the US customers the file mentions; worth a look.

Audit: instruction_file_audit.py on the new file reports no missing path, script or import, no credential, 0 notes (16 non-blank lines).
