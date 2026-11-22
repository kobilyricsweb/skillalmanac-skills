---
name: hotfix-release
description: Ships an emergency production fix for crm-web from the last release tag through the release branch, back to main, with changelog and incident note. Use when production is broken and the fix cannot wait for the next release, or the user says hotfix, urgent prod fix, patch production. Do not use for normal releases or for any change that is not a production break.
metadata:
  source: .cursor/rules/hotfix.mdc
---

# Hotfix release

A hotfix missing from main comes back as a regression in the next release, so every step below is required.

## Workflow

1. Branch from the last release tag, not from main: `git switch -c hotfix/<ticket> vX.Y.Z`.
2. Make the smallest possible fix. No refactors, no dependency bumps.
3. Check before tagging (see below).
4. Open a PR against the `release` branch. One reviewer is enough; say "HOTFIX" in the title.
5. After merge, tag `vX.Y.Z+1` on `release` and push the tag.
6. Bring the fix back to main with `git cherry-pick -x <sha>` so the commit message records where it came from.
7. Add a line to CHANGELOG.md under the new version.
8. Write the incident note in `docs/incidents/` within one working day.

## Rules that always hold

- Do not merge `release` into `main`.
- Do not skip the cherry-pick.
- Do not use the hotfix path for anything that is not a production break.

## Check before finishing

- [ ] The fix has a test that fails without it.
- [ ] `pnpm typecheck` and `pnpm test` pass on the hotfix branch.
- [ ] The on-call engineer has been told in #incidents.
