# Listing page content: backend-as-a-service-setup

**One line:** Sets up or audits a hosted-backend project's auth, rules, storage, keys and environments, with a read-only audit script.

## What it does

The skill gives an agent a seven-step procedure for a hosted backend (BaaS) where the browser or app talks to the database and storage directly: inventory, key classification, one project per environment, auth settings, default-deny data rules, storage modes, then verification. Decision tables choose auth providers, where access checks live (policies, server code, or both), and bucket modes. A key table separates public client keys from privileged ones and gives the rotation order after an exposure. A bundled script audits a project folder by reading file contents and prints strict JSON with file, line and variable name but never a secret value. A 12-test smoke plan covers the cross-user cases that catch real incidents.

## Capabilities

- `scripts/baas_audit.py`: finds privileged keys in env files that git tracks or ignores nothing, privileged values behind public-bundle prefixes, secret-looking values in source (client-side files graded critical), unconditional `allow` rules, time-bounded test-mode rules, signed-in-only rules, tables without row-level security, always-true policies, write grants to the anonymous role, missing rules files, and env files that drift or share values with production
- Decision tables for auth, access-check placement, storage, environments
- 12 smoke tests with expected outcomes and a results table
- A fixed report that lists the vendor claims relied on and what was not checked

## When to use

You are setting up a hosted backend or reviewing one before launch; you suspect a key leaked; you want rules or row-level policies written or checked; you need dev, staging and prod separated.

## When not to use

Self-hosted servers, schema and query tuning, data migration between vendors, scanning git history for secrets, or testing a system you do not own. Differs from configuration-key-drift-check (compares key sets across config files only) and sql-and-database-helper (queries and schemas): this skill is about the access boundary of a hosted backend.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual checks in step 7.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent edit to show. Real script output from the saved fixtures (`python evals/run_fixtures.py --write <folder>`, then the audit):

1. `python scripts/baas_audit.py bad_env`: exit 1, verdict fail, 4 files scanned, 5 critical, 1 high, 1 medium. First findings: `env_secret_not_ignored` at `.env` line 3 (key `SUPABASE_SERVICE_ROLE_KEY`, detected as a service-role JWT by decoding its role claim), line 4 (`STRIPE_WEBHOOK_SECRET`, secret by name), line 6 (`DATABASE_URL`, a URL with a password), and `env_public_var_secret` at `.env` line 5 (`NEXT_PUBLIC_ADMIN_SECRET`). No value appears anywhere in the output.
2. `python scripts/baas_audit.py bad_rules`: 16 findings including `rules_open` at `firestore.rules` line 6 (`read, write`), `rules_time_bounded_open` at line 12, `table_without_rls` for `notes`, `policy_open` for an update policy that is always true, and `rules_file_missing` for a storage rules file that firebase.json names but the folder lacks.
3. `python scripts/baas_audit.py good`: verdict pass, no findings, 9 files scanned.

## Limits

- Files only: live dashboard settings and deployed rules are not visible.
- Policy checks are text patterns; only cross-user smoke tests prove a policy is right.
- Git history is not searched.
- Reads Postgres-style SQL, Firestore-style rules, Realtime-database-style JSON rules, firebase.json, appwrite.json and a Supabase-style config.toml; other formats are not read.
- Placeholder-looking values (example, changeme, your-...) are ignored.
- Numeric values are working starting points, not vendor limits; vendor-specific claims are marked unconfirmed.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN; 24 script fixture checks pass; the git-index reader matched `git ls-files` on one real repository (1,922 paths). Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool install, human review, accuracy of any vendor claim against live docs.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Point the agent at a project folder with "check this before we launch"; it runs the audit: verdict fail, 5 critical.
2. It lists findings by variable name and line, never showing a value, and orders the fix: rotate, then ignore, then clean history.
3. It rewrites an always-true update policy into owner using plus with-check, and re-runs the audit.
4. It hands over the 12-test smoke plan and a report that names what was not checked.

## FAQ seeds

- Does it print my keys? No: the script reports names, files and lines only, and the skill forbids the agent from opening env files to show values. Fixture checks confirm no fake secret appears in the output.
- Does it need network access? No.
- Does it work for my vendor? The procedure is vendor-neutral; the script reads common file formats of three vendor families. Vendor-specific claims are marked for you to verify.
- Does a pass mean my backend is secure? No. It means the files show none of the patterns it knows. Run the smoke tests against dev and staging.
- Will it find secrets already in git history? No. Rotate any key that was ever committed; use a history scanner for the rest.
- Is the anon or publishable key a secret? No, but it must be paired with rules that assume it is hostile.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
