# Storefront: LEGACY_BILLING flag, unused dependencies, removal plan

Nothing has been run. Below is the delegation decision, the exact prompts I would send, and how I would check the results. Both prompts are final; tell me to go and I send them.

## 1. What I delegate and what I keep

| Piece | Decision | Reason |
|---|---|---|
| Find every read of LEGACY_BILLING | Delegate (agent A) | Search-heavy, output the caller does not need to keep, read-only. |
| Find unused npm dependencies | Delegate (agent B) | Independent of A, also search-heavy, read-only. Different method (per-package usage check), so a separate agent is cleaner than one agent doing both. |
| A and B | Send together, in parallel | Neither needs the other's result. |
| Removal plan | Keep with me, written after A and B return | It is the synthesis. It depends on A's list of read sites (each one needs a decision about which branch survives), and an agent that has not seen this conversation would plan a different problem. So no brief is written for it now. |

Agents used: 2 (A and B). No third agent for the plan. Both are read-only and can run on a small, fast model, since the work is search and quoting, not judgement.

I skimmed the ten files in storefront/ only to write the "Watch for" lists below. I am not claiming any findings. The hints in the prompts are marked as things to verify.

## 2. Prompt for agent A: all reads of LEGACY_BILLING

```
Goal: Find every place in storefront/ that reads, sets or mentions the LEGACY_BILLING flag, including indirect reads. It is needed because the flag is going to be removed and the removal plan must list every site that has to change, so a missed site means a broken or half-removed flag.

Scope: look in storefront/ (source, tests, docs, deploy and config files, package.json scripts, any dotfiles such as .env*, Dockerfiles, CI files). Leave everything outside storefront/ alone.

Already known (verify, do not assume): the flag is probably defined in storefront/src/config/flags.js and exported from there, and a deploy file under storefront/deploy/ may set it as an environment variable. These are hints only; confirm each one yourself and do not stop at them.

Watch for:
- Direct reads: flags.LEGACY_BILLING, process.env.LEGACY_BILLING, destructured imports.
- Indirect reads: the name built from string pieces (for example 'LEGACY_' + 'BILLING'), bracket access flags[key], template strings, lowercase or camelCase variants (legacyBilling, legacy_billing), and anything that re-exports or copies the flags object and is read elsewhere.
- Writers, not only readers: tests that set the env var before requiring a module, deploy values, env files, CI settings.
- Docs and comments that mention the flag by name.
- Code paths that are only reachable through the flag (for example a function called only from the flagged branch); list them as "dead if flag removed" but do not judge them beyond that.
- Search case-insensitively and for fragments ("LEGACY", "BILLING") so a split name is caught.

Constraints: read-only; do not create, edit or delete files. You may run: grep/rg, find, ls and cat-style file reads inside storefront/. Do not run npm, node or any test.

Done when: you have searched all file types in scope with the patterns above, and every hit is classified. Stop there; do not propose fixes.

Return exactly:
RESULT: FOUND <n> sites (<r> reads, <w> writes/definitions, <d> docs/comments) or NOT FOUND
EVIDENCE:
- <file>:<line> - <quoted line> - <classification: direct-read | indirect-read | definition | deploy-config | test-setup | doc | dead-if-removed>
VERIFIED BY: <the exact searches or commands you ran>
NOT CHECKED: <what you could not cover, or "nothing">
At most 40 lines. No narrative.
```

## 3. Prompt for agent B: unused npm dependencies

```
Goal: Determine which dependencies and devDependencies declared in storefront/package.json are unused. It is needed because the caller will decide which packages to drop from the manifest, and a false "unused" would break the build or production.

Scope: look in storefront/ (package.json, src/, test/, deploy/, docs/, any config files, any scripts in package.json). Leave everything outside storefront/ alone.

Already known (verify, do not assume): package.json lists a handful of runtime dependencies and one dev dependency. I have not established which are used. Treat every one as undecided and check each separately.

Watch for:
- A package that is imported or required but whose imported names are never used (an import is not a use; report it as "imported-not-used" with the line).
- A package used only in tests, or only by tooling (for example a test runner that is invoked through a script or CLI and never imported). A dev dependency can be used without being imported anywhere.
- Usage through require() with a variable, dynamic import(), or a package named in a script, config file or Dockerfile.
- Packages used only in dead or flag-guarded code; mark the usage as such.
- Packages that are transitive dependencies of another listed package; mention but do not count as usage.
- Do not rely on a lock file or node_modules existing; check by reading the source.

Constraints: read-only; do not create, edit or delete files. You may run: grep/rg, find, ls and file reads inside storefront/. Do not run npm install, npm uninstall, npx or any test, and do not use network.

Done when: every entry in dependencies and devDependencies has a verdict backed by a search you ran.

Return exactly:
RESULT: <n> of <total> declared packages unused
EVIDENCE (one line per declared package):
- <package>@<version> - <used | imported-not-used | tooling-only | unused> - <file>:<line> - <quoted line, or "no references found by: <search>">
VERIFIED BY: <the exact searches or commands you ran>
NOT CHECKED: <what you could not cover, or "nothing">
At most 25 lines. No narrative.
```

## 4. How I will check the results

Returned work is a claim, so before using it I will:

1. Open three of A's cited locations and confirm the quoted line is really there. At least one must be an indirect read if A reports any, and one must be a non-code file (deploy or test).
2. Run one independent search myself for the flag name, case-insensitive and for the split fragments, and confirm the count matches A's. If A says NOT FOUND, I treat it as unproven until my own search agrees.
3. For B, pick two packages marked unused and grep for each name across storefront/ to confirm no reference, and pick one marked used and confirm the cited line is a real use rather than an unused import.
4. Check that each agent stayed read-only (git status shows no changes in storefront/).

## 5. The removal plan (written after A and B return)

I do not write the plan from guesses. Once A's evidence is checked, the plan will be structured as follows:

1. Decide the surviving behavior: confirm with the owner that the new billing path wins in every environment, and confirm production's current setting from the deploy config.
2. One change per read site, ordered: the code branches first (keep the new path, delete the legacy function and the dead code it leaves), then the test that forces the legacy path, then the flag definition, then the deploy setting, then the docs.
3. Safety steps: remove the deploy variable only after the code no longer reads it, and have a rollback (revert the commit) ready.
4. Cleanup from B: packages that become unused after the legacy code is gone are added to the removal list only after re-running B's check on the final code.
5. Verification: run the test suite and exercise a charge and an invoice render in staging, then confirm no hits remain for the flag name.

Open question for you: is the new billing path already live for all customers? The plan's order depends on it.
