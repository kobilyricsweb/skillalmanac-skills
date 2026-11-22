# Proposed subagent run for storefront/ (nothing has been run)

No agent skills are installed under `.claude/skills/` in this workspace, so no skill applies.

## Structure

- **Agent A (flag readers)** and **Agent B (unused dependencies)** are independent and read-only. They would run in parallel.
- **Agent C (removal plan)** needs A's findings, so it would run after A. It does not need B. A short note about `pg` could be passed to it, because `charge.js` imports `pg`.
- All three are read-only, except that C writes one plan file.

I took a quick look at the files to make the prompts concrete. This is a hint only, not a replacement for the agents' work. The flag appears in `src/config/flags.js`, `src/billing/charge.js`, `src/billing/invoice.js`, `test/charge.test.js`, `deploy/values.yaml` and `docs/billing.md`. `invoice.js` builds the key dynamically (`'LEGACY_' + 'BILLING'`), so a plain grep for the literal flag name would miss it. `package.json` lists express, lodash, moment, pg, left-pad and jest.

---

## Prompt A: find every place that reads LEGACY_BILLING (Explore agent, run in parallel with B)

```
Working folder: storefront/ only. Read-only: do not edit, create or run anything.

Goal: list every place that READS the LEGACY_BILLING flag, directly or indirectly.

Search for:
1. The literal string LEGACY_BILLING in all files (code, tests, config, YAML/JSON, docs, Dockerfiles, CI files, .env files).
2. process.env access (dot and bracket form) and any wrapper module that re-exports the flag. Identify the flag module and then find every importer of it.
3. Dynamic or obfuscated access that a literal grep misses: string concatenation or template literals building the key, computed property access such as flags[key], destructuring, and case or prefix variants (legacyBilling, LEGACY_, billing.legacy).
4. Places that only SET the flag (deploy values, test setup) versus places that READ it. Report them in separate groups.

For every hit give: file path, line number, the exact line, and a classification (reader / setter / doc-only). For each reader, say what behaviour changes when the flag is on versus off.

Finish with a list of the files you searched and the search patterns you used, plus anything you could not determine. Do not guess: if a hit is ambiguous, say so.
```

## Prompt B: unused npm dependencies (general-purpose, read-only, run in parallel with A)

```
Working folder: storefront/ only. Read-only: do not edit, install, or run any package manager or the test suite.

Goal: determine which dependencies in storefront/package.json are unused, checking independently of any work on feature flags.

For EACH entry in dependencies and devDependencies:
1. Search the whole project for usage: require('x'), import ... from 'x', dynamic import('x'), and subpath imports ('x/sub').
2. For devDependencies, also check scripts in package.json and any config file (jest config, CI files) for CLI use. Jest is run by the test script or by name, not by require.
3. Distinguish three states: used (imported and actually referenced), import-only (imported but the binding is never used), and not referenced at all.
4. Also note any package that is only used in test files, or only in a file that is itself unreachable from the entry point (src/server.js).

Output a table: package | version | verdict (used / import-only / unused) | evidence (file:line) | confidence. Give the verdict from what you read, not from assumptions about what a package is typically used for. Note any caveat, such as usage you could not rule out through dynamic loading.
```

## Prompt C: plan to remove the flag (Plan agent, run after A finishes)

```
Working folder: storefront/ only. Do not edit code; produce a plan only.

Input: the findings report from the flag-readers investigation (paste it here: all readers, setters, and docs). Use only those findings plus your own reading of the files they cite. If you find a reader that report missed, flag it.

Decision to plan around: the legacy processor path is retired and the new path becomes the only behaviour. Confirm this assumption against the code before relying on it.

Write a removal plan with:
1. Ordering: which changes can ship first with no behaviour change (for example setting the flag off in deploy config and confirming) and which delete code. Say why the order matters for rollback.
2. Per-file change list: for each reader, the exact branch to keep and the branch/function to delete (for example legacyCharge, the invoice_v1 template path, the flags.js entry), including the dynamic-key read.
3. Non-code cleanup: deploy/values.yaml env entry, docs/billing.md, test setup in test/charge.test.js (which currently forces the legacy path and so needs rewriting for the new path).
4. Risks and checks: anything still depending on legacy behaviour (invoice_v1.html consumers, in-flight orders), and how to verify nothing reads the flag afterwards (a final grep including the concatenated-key form).
5. Rollback plan per step and a definition of done.

Keep it short and numbered. State open questions for the owner separately instead of guessing.
```

## What I would hand back after running

1. A reader list from A, flagging the dynamic read in `invoice.js`.
2. A dependency verdict table from B.
3. The removal plan from C, built on A's findings.
