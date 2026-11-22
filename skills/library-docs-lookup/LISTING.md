# Listing page content: library-docs-lookup

**One line:** Makes an agent answer library questions from the installed package's own files, with file and line cited.

## What it does

The skill gives an agent a six-step procedure: name the package and import path, locate the installed version and its local docs, read them in a fixed order (types, entry file, README, changelog, source), check the changelog when the version matters, answer in a fixed format with an evidence label, and verify any code it wrote. A read-only script does the locating: given a project folder and a package name it reads lockfiles and installed metadata, reports the version that actually runs, flags disagreement between lock and installed copy, and lists the README, type declarations, entry file, changelog and docs files on disk, with line counts. Output is one strict JSON object.

## Capabilities

- `scripts/find_local_docs.py`: version from `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `poetry.lock`, `uv.lock`, `requirements*.txt`, `go.sum`/`go.mod`, `vendor/`, `node_modules` (including pnpm store and `@types`) and virtualenv `dist-info/METADATA`, each with the file and line to cite
- Warnings for lock/installed mismatch, missing declared type files, deprecated packages, Go `replace`, Yarn Plug'n'Play
- A decision table for what to do when nothing is installed
- Four evidence labels (`LOCAL-VERIFIED`, `LOCAL-ABSENT`, `CHANGELOG-ONLY`, `UNVERIFIED`) and a fixed answer format

## When to use

The agent invents a function, option or signature; you say "that method doesn't exist in this version", "what changed in v3", "read the real API"; or code broke after an upgrade and you need the installed version's behaviour.

## When not to use

Language or framework tutorials, picking between libraries, upgrading dependencies, writing docs for your own library, or packages that are not installed and may not be fetched. It does not browse the web.

Differs from docs-fetching tools: it uses no network and reads what is on disk for the pinned version, so it cannot reach docs that were never installed, but it also cannot return the wrong version's docs.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual fallback commands in step 2.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of the script (fixture run, project path shortened) for "a teammate says acme-widgets 2.4.0 is in use":

```
python scripts/find_local_docs.py evals/fixtures/p_npm_mismatch acme-widgets
{ "found": true, "resolved_version": "2.3.1", "resolved_from": "installed", "version_mismatch": true,
  "versions": [
    { "kind": "locked",    "version": "2.4.0", "file": "package-lock.json", "line": 5 },
    { "kind": "installed", "version": "2.3.1", "file": "node_modules/acme-widgets/package.json", "line": 3 } ],
  "docs": [ { "kind": "types", "path": "node_modules/acme-widgets/index.d.ts", "lines": 1 } ],
  "warnings": [
    "node_modules/acme-widgets declares types file ./missing/index.d.ts that is not on disk",
    "installed, locked or pinned versions disagree (2.3.1, 2.4.0): code runs against the installed copy; tell the user" ] }
```

Second run (Python fixture) for "what is the signature of acme_tools.slugify and which version do I run":

```
resolved_version 1.4.2 (installed, .venv/.../acme_tools-1.4.2.dist-info/METADATA line 3)
requirements.txt line 2 pins 1.4.0, poetry.lock line 3 says 1.4.2, version_mismatch true
docs: METADATA, acme_tools/__init__.py (5 lines), py.typed, __init__.pyi (1 line)
```

No saved agent answer exists yet: the task evals in `evals/evals.json` have not been run, so no with/without comparison is shown.

## Limits

Copied from the skill: no `pyproject.toml` ranges, Pipfile.lock, conda, global installs, Go module cache (use `go list` and `go doc`), Yarn Plug'n'Play archives, Deno, Bun or other ecosystems. The script lists files and does not read their content. Lockfile parsing is line-based, so a miss is not proof of absence. Local docs can be stale or thin.

## Evidence

Static lint and fixture run only; see VERIFICATION.md. Not tested: with/without efficacy, triggering, any tool other than the authoring session, any human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Use acme-widgets to make a widget with a color." The baseline agent writes `createWidget({ size, color })`.
2. With the skill: the agent runs the locator, sees 2.3.1 installed, opens `dist/index.d.ts`.
3. It reports `LOCAL-ABSENT`: options are `size` (required) and `label` (optional), cites `dist/index.d.ts:1`, lists what it searched.
4. Close on the Not checked line and the version note about a newer lock entry.
(Storyboard only; to be recorded from a saved real run once the task evals exist.)

## FAQ seeds

- Does it need network? No.
- Does it install packages? No; it asks you to, with your own command.
- Does it work without Python? The procedure does; the agent uses `npm ls`, `pip show` or `go list` by hand.
- How is it different from a docs-fetch tool? It reads the pinned version on disk and never goes online.
- What if the package is not installed? The answer is labelled UNVERIFIED and says what would have been read.
- Which languages? npm, Python and Go lookups; the reading procedure applies to any.
- What data leaves my machine? None.
- How do I uninstall it? Delete the skill folder.

## Changelog

0.1.0, 2026-11-21: first draft, lint and fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings. Drafted with AI assistance (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
