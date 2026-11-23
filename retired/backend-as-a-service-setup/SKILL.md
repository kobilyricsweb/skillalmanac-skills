---
name: backend-as-a-service-setup
description: Sets up or audits a hosted backend (BaaS) project so auth, database rules, storage and environments are safe on the first deploy, using decision tables, a secrets and key-handling procedure, a smoke-test plan and a read-only audit script that finds committed secret keys, open rules, tables without row-level security and drifting env files. Use when the user says set up auth and a database, row-level security, security rules, service key leaked, anon key, dev staging prod, or check my backend before launch. Do not use for self-hosted server design, schema or query tuning, or pen-testing someone else's system.
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
compatibility: The audit script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checks in step 7.
---

# Backend-as-a-service setup

A hosted backend lets the browser or app talk to the database and storage directly. That moves the security boundary from your server code to rules, policies and keys. Almost every first-deploy incident is one of five things: a privileged key in the client or in git, a table with no policy, a rule that is open to everyone, dev and prod sharing one project, or a public storage bucket holding private files. This skill closes those five.

Vendor facts below that are not marked are true of the whole category. Anything tied to one vendor says "verify against vendor docs (unconfirmed)": the names and defaults change, and this package was not checked against live vendor consoles. Source pages are listed in [references/sources.md](references/sources.md).

## Hard rules for the agent

- Never print, paste, log or `cat` a secret value, and never ask the user to paste one into chat. Work with variable names and file paths. The audit script prints names and line numbers only.
- Never run write tests against production. Smoke tests run on dev or staging with throwaway users.
- A key that was ever committed or pasted somewhere shared is compromised: rotate it, do not just delete it.
- The privileged key (service role, secret key, admin SDK credential, service-account file) lives only in server-side config. See the key table in step 2.

## Workflow

```
- [ ] 1 Inventory: run the audit, read the existing config
- [ ] 2 Keys: classify every key public or privileged
- [ ] 3 Environments: one project per environment
- [ ] 4 Auth: provider choice and settings
- [ ] 5 Data access: default deny, policies per table
- [ ] 6 Storage: bucket mode, path rule, limits
- [ ] 7 Verify: audit again, smoke tests, report
```

1. **Inventory.** If a project folder exists, run `python scripts/baas_audit.py <folder>` and keep the JSON. Fix criticals before anything else (step 2). If there is no folder yet, skip to step 2 and write the files from the tables below.
2. **Keys.** Classify each key, then place it:

| Kind | Examples of the kind | May live in | Never in |
|---|---|---|---|
| Public client key | anon or publishable key, web API key, project id, app id | client bundle, public env vars, git | nothing to hide, but restrict it: allowed domains or bundle ids, and rules or policies that assume it is hostile |
| Privileged key | service role key, secret key, admin SDK or service-account file, JWT signing secret, database URL with password | server env, CI secret store, platform secret manager | client bundle, `NEXT_PUBLIC_`-style variables, git, logs, chat, mobile app binaries |

   A variable name with a client-bundle prefix (`NEXT_PUBLIC_`, `VITE_`, `EXPO_PUBLIC_` and similar; verify the list for your framework) is public by construction. Any privileged value behind such a prefix is a leak, even in a private repo. If a privileged key was exposed, rotate in this order: issue the new key, update the secret store, redeploy, run the smoke tests, revoke the old key, then check provider logs for use of the old one. Deleting the file or rewriting git history comes after rotation, not instead of it. Some vendors invalidate all sessions when the JWT signing secret rotates: verify against vendor docs (unconfirmed).
3. **Environments.** One backend project per environment: dev, staging, prod. Same key names in every environment, different values. Never point a dev or preview build at the prod project to "see real data". Per environment:

| Item | dev | staging | prod |
|---|---|---|---|
| Data | seed or fake | seed or anonymised | real; nothing copied out of it |
| OAuth client and redirect URLs | own client, localhost URLs allowed | own client, staging host only | own client, exact prod URLs, no localhost, no wildcards |
| Email and SMS provider | sandbox or log-only | sandbox | real, with sender domain set up (SPF, DKIM) |
| Sign-ups | open | as prod | as intended; invite-only if internal |
| Rules and policy deploys | by hand allowed | CI only | CI only, after staging passes the smoke tests |
| Dashboard access | team | team | two named people, MFA on |
| Backups and billing alerts | off | off | on; verify the vendor's backup tier (unconfirmed) |

   File layout: `.env.example` (placeholders, committed), `.env.development`, `.env.staging`, `.env.production` (ignored by git, or better, held only in the platform secret store). `.gitignore` needs `.env*` and `!.env.example`. The audit flags key-set drift between the files and values shared with production.
4. **Auth.** Pick providers from the table, then apply the settings checklist.

| Situation | Use | Watch for |
|---|---|---|
| Consumer app, low friction | email magic link or one-time code, plus one social login | If the iOS app offers any third-party social login, the app store may require an equivalent privacy-preserving option: verify against current store rules (unconfirmed) |
| B2B product | email plus password with MFA, SSO (SAML or OIDC) for larger customers | SSO is often a paid tier: verify against vendor docs (unconfirmed) |
| Internal tool | the company identity provider, restricted to the company email domain, email sign-up disabled | Allowed-domain list must be enforced server-side, not in the UI |
| Trial before sign-up | anonymous sessions, later linked to a real account | Anonymous users are authenticated: policies that only test "signed in" admit them |
| Phone one-time codes | only where needed | SMS cost abuse: captcha, per-IP and per-number rate limits, country allow-list |

   Settings checklist: email confirmation required before access; redirect-URL allow-list holds exact URLs only; passwords at least 8 characters with a breached-password check (the NIST SP 800-63B baseline, not a vendor default); access-token lifetime at most 1 hour with refresh-token rotation on (working value; verify the vendor default); captcha or rate limit on sign-up, sign-in, reset and code-send endpoints (starting point: 5 sign-ups per hour per IP, tune with real traffic); MFA on every admin account; one OAuth client per environment. Account-linking trap: link two providers on the same email only when the provider reports that email as verified; otherwise a stranger who registers your user's email elsewhere takes the account over.
5. **Data access.** Default deny: enable row-level security (or the vendor's rules) on every table and collection first, then add the narrowest policies. Choose where checks live:

| Situation | Check goes in | Reason |
|---|---|---|
| Browser or mobile app reads and writes the database directly | rules or row-level policies, always | nothing else stands between the user and the data |
| Only your own server touches the database, with the privileged key | app code, and still enable deny-all rules | the key bypasses rules, so the app code is the only check; deny-all protects you if the public key is ever used on that table |
| Multi-tenant data | policy comparing the row's tenant id with a claim that only the server can set | a claim the user can edit (profile or "user metadata" fields) lets a user choose their own tenant: verify which fields are user-editable on your vendor (unconfirmed) |
| Quotas, state machines, cross-table rules | server function with the privileged key, rules limited to ownership | rules cannot express them reliably |
| Public read content | one read policy on that table only; writes closed | |
| Admin screens | server-side role check; no privileged key in the admin client | |
| Leaderboards, counts | a view or function exposing only the needed columns | opening the table would expose every column |

   Policy pattern for an owned table, as pseudo-SQL (adapt per vendor): column `owner` not null, default the caller's id. Read: `owner = caller`. Insert: with-check `owner = caller`. Update: using `owner = caller` AND with-check `owner = caller` (without the with-check a user can hand a row to someone else). Delete: using `owner = caller`. Traps: a read policy of `true` on a table with private columns; a policy that tests only "signed in"; views that run with their creator's rights and bypass policies (verify the invoker setting on your vendor, unconfirmed); privileged database functions without a pinned search path; rules that read other documents cost reads and have per-request limits (verify, unconfirmed).
6. **Storage.** Default every bucket to private.

| Content | Mode | Path and access rule | Limits |
|---|---|---|---|
| Avatars, marketing images | public read | write only to `avatars/<user id>.<ext>` | image types only, at most 2 MB |
| User documents | private | `<user id>/...` prefix equals caller; download by signed URL | signed URL lifetime 60 to 300 seconds; size cap per use case |
| Shared with a group | private | membership lookup in the policy, or the server mints the signed URL | |
| Content other users will see | private upload, server review, then publish | never let the uploader choose the public path | |
| Exports, backups | private, no client policy | privileged key only; lifecycle expiry | |

   Set allowed MIME types and maximum size at the bucket, not in the client. Do not serve user HTML or SVG from your app origin: serve as a download or from a separate domain. A public bucket's URLs stay cached after deletion; treat anything put there as permanent. The audit reports public buckets it can see in config.
7. **Verify.** Run `python scripts/baas_audit.py <folder>` again, fix, re-run until no critical or high remain. Then write the smoke tests from [references/smoke-tests.md](references/smoke-tests.md) (12 tests; the cross-user ones are the ones that catch real incidents) and give the user the commands to run against dev and staging with their own keys. If Python cannot run, check by hand: `.env*` in `.gitignore`; no privileged key behind a public prefix; every table has deny-all plus owner policies; no rule or policy that is unconditionally true except an intended public read; env files have the same key names.

## The audit script

`python scripts/baas_audit.py <folder> [--fail-on critical|high|medium|never]`: run it, do not edit it. Read-only; standard library; no network and no git command. It reads file contents (key patterns, JWT role claims, policy text), `.gitignore` files and the `.git/index` file. Exit 0: nothing at or above the threshold (default high); 1: something is; 2: bad usage. Output is one strict JSON document:

```json
{"tool": "baas_audit", "version": "0.1.0", "root": "...", "git": {"repo_found": true, "index_readable": true},
 "files_scanned": 0, "truncated": false, "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
 "verdict": "pass|review|fail", "not_checked": ["..."],
 "findings": [{"id": "F001", "severity": "critical", "category": "...", "file": "rel/path", "line": 3,
               "key": "VARIABLE_OR_RULE_NAME", "detail": "...", "fix": "..."}]}
```

Verdict: fail if any critical or high, review if only medium, else pass. Values are never in the output, not even a prefix or a length. Categories and what each means: [references/audit-findings.md](references/audit-findings.md); read the entry for a category when you act on it. Findings are patterns, so judge each one: a `rules_open` read rule can be an intended public catalogue.

## Report format

```
Verdict: <pass | review | fail>, from the audit run on <date>
Fixed: <what changed, by finding id>
Rotate now: <keys that were exposed, in the rotation order from step 2; names only>
Open: <findings left, with the reason, e.g. intended public read>
Unconfirmed vendor claims: <list the "verify" items you relied on>
Not checked: <live dashboard settings, deployed rules, git history, anything the smoke tests did not run>
```

## Limits

- Files only: the live dashboard, deployed rules and provider settings are invisible to the script. A clean audit does not mean the deployed backend is safe.
- Policy and rule checks are text patterns. A policy can look restrictive and be wrong (a wrong column, a missing tenant check). Only the cross-user smoke tests show that.
- Git history is not searched. A secret deleted from the tree may still be in old commits and clones.
- Row-level policy parsing covers Postgres-style SQL files, Firestore-style `.rules`, Realtime-database-style rules JSON, `firebase.json`, `appwrite.json` and a Supabase-style `config.toml`. Other vendors' formats are not read.
- Values containing the words example, changeme, your-... are treated as placeholders and ignored; a real key with such a word in it is missed. Files over 1 MB and folders like `node_modules` and `dist` are skipped; scans stop at 20,000 files and say so.
- Numeric values (token lifetime, signed-URL lifetime, sign-up rate) are working starting points, not vendor limits.
- Not legal or compliance advice (GDPR, HIPAA, PCI). Not a penetration test; do not run the smoke tests against systems you do not own.
