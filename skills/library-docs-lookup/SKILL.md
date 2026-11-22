---
name: library-docs-lookup
description: Answers questions about a library's API from the copy installed in the project instead of from memory, using a read-only script that finds the installed version in lockfiles and lists the local README, type declarations, source and changelog, then cites file and line. Use when an agent invents a function, option or signature, the user says wrong method, hallucinated API, doesn't exist in this version, what changed in v3, how do I call this package, or code broke after an upgrade. Do not use for language or framework tutorials, choosing between libraries, upgrading dependencies, or packages that are not installed.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual fallback in step 2.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Library docs lookup

Answer from the files on disk, for the version the project actually runs. Web pages and memory describe the latest release or an older one; the installed copy describes the code that will execute.

## Rules

1. Never write a signature, option name, default value or return type you have not read in a local file during this task.
2. Every claim about a library carries `path:line` and the version. Take line numbers from the Read or search output, never from estimation.
3. If the symbol is not in the installed files, say so. Do not fill the gap with a plausible name.

## Workflow

```
- [ ] 1 Name the package, the import specifier and the symbol
- [ ] 2 Run the locator and read its JSON
- [ ] 3 Read local files in the fixed order
- [ ] 4 Check the changelog when the version matters
- [ ] 5 Answer in the fixed format
- [ ] 6 Verify any code you wrote
```

1. **Name it.** Write down the package name as the lockfile spells it (`@scope/name` for npm, the distribution name for Python, the module path for Go), the exact import specifier from the user's code (`pkg/server` is a different file from `pkg`), and the symbol in question.
2. **Locate.** Run `python scripts/find_local_docs.py <project_dir> <package>` (add `--ecosystem npm|python|go` when the name exists in several). Do not edit the script to change its result. Read these fields first: `resolved_version`, `resolved_from`, `version_mismatch`, `warnings`, then `docs`. Decide with this table:

| Result | Do |
|---|---|
| `resolved_from` is `installed` | Proceed. This is the version that runs. |
| `version_mismatch` is true | Proceed with the installed copy and tell the user the lock or pin disagrees; their next install will change behaviour. |
| `resolved_from` is `locked`, `pinned` or `declared`, nothing installed | Stop guessing. Ask the user to install dependencies with their own install command, or say your answer is unverified (step 5 label `UNVERIFIED`). |
| `found` is false (exit 1) | Check the spelling, other ecosystems, a monorepo root. Never answer from memory as if it were found. |
| Warning about Plug'n'Play, `replace`, or deprecated | Read the warning aloud in the answer; it changes where the code comes from. |

   Without Python: npm, open `node_modules/<pkg>/package.json`; Python, `pip show -f <pkg>` with the project's own interpreter (prints Version and Location, offline); Go, `go list -m -f "{{.Version}} {{.Dir}}" <module>` (works only if already downloaded). Then open the same files the table in step 3 names.
3. **Read in this order**, stopping once the question is settled. Read the region around the symbol (about 40 lines either side), not whole files; search a file larger than 2,000 lines by name first.

| Order | File kind in `docs` | Gives you | Trap |
|---|---|---|---|
| 1 | `types` (`.d.ts`, `.pyi`, Go source) | Exact signatures, optional vs required, overloads | The `.d.ts` must be the one for your import specifier. Subpath imports have their own. `@types/*` is a separate package whose version tracks only major.minor. |
| 2 | `entry` (`main`/`module`, `__init__.py`) | Whether the name is exported at all, re-exports, lazy `__getattr__` | Absence in `__init__.py` is not proof; search the package folder before concluding. |
| 3 | `readme`, `docs_dir` | Intended usage | Written for this version, but examples can lag the code. When README and types disagree, types win. |
| 4 | `changelog` | Renames, removals, defaults changed | Section headings are versions; read only the ones in range (step 4). |
| 5 | `source` | Real behaviour: defaults, thrown errors, side effects | Only needed when 1 to 3 do not answer. Behaviour beats prose. |

   More detail per ecosystem: [references/where-docs-live.md](references/where-docs-live.md). Read the section for the ecosystem in use only.
4. **Changelog check.** Read the changelog when any of these holds: the user's code or an example was written for another major version; `version_mismatch` is true; the symbol exists but behaves differently than the user expects; the user asks what changed. Read the entries from the older version to `resolved_version` only. If there is no local changelog, look for a `project_urls` or `homepage` field in `installed` and tell the user which page to open; do not browse unless the user allows it, and say the result is then not from local files.
5. **Answer** in the format in [references/answer-format.md](references/answer-format.md): one verdict line with a label, the cited lines, the version, what you did not check. Labels: `LOCAL-VERIFIED` (symbol read in an installed file), `LOCAL-ABSENT` (searched, not there), `CHANGELOG-ONLY` (known from release notes, not seen in code), `UNVERIFIED` (nothing local; stated as such).
6. **Verify code you wrote.** For each library name in your code, confirm it appears in a cited file with the argument order and required fields you used. Run the project's type checker or tests when they exist and are quick; report if you did not.

## Script contract

`python scripts/find_local_docs.py <project_dir> <package> [--ecosystem all|npm|python|go]` reads only; it writes nothing, runs no subprocess and uses no network. stdout is one strict JSON object:

```
{ "tool": "find_local_docs", "schema_version": 1, "project": str, "package": str,
  "ecosystems_with_hits": [str], "found": bool, "resolved_version": str|null,
  "resolved_from": "installed"|"locked"|"pinned"|"declared"|"checksum_listed"|null,
  "version_mismatch": bool,
  "versions": [{ "ecosystem", "kind", "version", "file", "line": int|null, "note"? }],
  "installed": [{ "ecosystem", "path", "version", "homepage"?, "repository"?,
                  "requires_python"?, "project_urls"?, "role"? }],
  "docs": [{ "ecosystem", "kind", "path", "bytes", "lines": int|null, "note"? }],
  "warnings": [str] }
```

`kind` in `versions` is one of `installed`, `installed_types`, `locked`, `locked_nested`, `pinned`, `declared`, `checksum_listed`. Paths are relative to the project, with forward slashes. Exit 0 found, 1 not found, 2 usage error (JSON with an `error` key). Supported lookups: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `node_modules` (also pnpm's `.pnpm` store and `@types`); npm, pnpm, Yarn, poetry and uv lockfiles and `node_modules` are also searched in up to 3 parent folders for workspaces, `requirements*.txt`, `poetry.lock`, `uv.lock`, virtualenv `site-packages` with `dist-info/METADATA`, `go.mod`, `go.sum`, `vendor/`.

## Limits

- Not read: `pyproject.toml` dependency ranges, `Pipfile.lock`, conda environments, system-wide Python or global npm installs, the Go module cache (use `go list`/`go doc` for it), Yarn Plug'n'Play archives, Deno and Bun caches, Maven, Cargo, Gradle, Composer and others.
- The script lists where files are. It does not read their content, judge their accuracy or find the symbol; steps 3 to 6 are yours.
- Lockfile parsing is line-based on the documented layouts; an unusual lockfile may be missed, so a miss is a reason to look by hand, not proof the package is absent.
- Local docs can be wrong, stale or thin. A local README may not mention a symbol the types contain.
- Generated or minified bundles can hold the symbol with no readable signature; say so and fall back to the types.
- Never run the project's install command, or fetch anything, without the user's approval.
