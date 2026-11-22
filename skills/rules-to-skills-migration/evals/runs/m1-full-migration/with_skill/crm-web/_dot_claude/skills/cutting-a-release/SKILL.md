---
name: cutting-a-release
description: Cuts a regular crm-web release, covering version bump, changelog, tag, deploy-prod watch, rollback and announcement. Use when the user asks to release, cut a release, bump the version, tag a version or publish the changelog. Do not use for emergency production fixes (use hotfix-release).
metadata:
  source: .cursor/rules/release-process.mdc
---

# Cutting a release

1. Make sure `main` is green in CI.
2. Run `pnpm version minor` (or `patch`). This bumps package.json and creates the commit.
3. Run `pnpm release:notes` to generate the CHANGELOG.md entry from merged PR titles. Edit it by hand: remove chores, group by area.
4. Tag `vX.Y.Z` and push the tag. The `deploy-prod` workflow starts from the tag.
5. Wait for `deploy-prod` to finish. If the smoke step fails, do not retry: roll back with the `rollback-prod` workflow and open an incident.
6. Post the changelog entry in #releases.

## Rules that always hold

- Never release on a Friday after 14:00 local time.

## Check before finishing

- [ ] `deploy-prod` finished with the smoke step green, or `rollback-prod` ran and an incident is open.
- [ ] The changelog entry is posted in #releases.
