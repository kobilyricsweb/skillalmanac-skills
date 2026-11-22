## Contents

- How to read a finding
- Secrets and env files
- Rules and policies
- Environment consistency

# Audit findings: category guide

Every finding has `severity`, `category`, `file`, `line` (null for formats without useful lines), `key` (a variable, rule or table name, never a value), `detail` and `fix`. Severity is the default; raise or lower it with the context you know and say why in the report.

## How to read a finding

- critical: act before anything else; rotate or close now.
- high: fix before launch.
- medium: fix soon, or record why not.
- low and info: awareness; often intended.

## Secrets and env files

| Category | Default severity | Meaning | What to do |
|---|---|---|---|
| `env_secret_tracked` | critical | An env file that git tracks holds a privileged value | Rotate the key. `git rm --cached <file>`, ignore it, commit. Old commits still hold the value, so rotation is the real fix |
| `env_secret_not_ignored` | critical | Privileged value in an env file no `.gitignore` rule covers; git index showed it as not tracked, or the index was unreadable | Add the ignore rule now, before the first commit. If a commit already happened, treat as tracked |
| `env_public_var_secret` | critical (high if the value is a placeholder) | A variable with a client-bundle prefix is named for a secret or holds one | Drop the prefix, move to server-only config, rotate if it ever shipped. A placeholder under such a name is a design mistake that will be filled in later |
| `env_example_real_value` | high | The committed template contains a real-looking secret | Replace with a placeholder; rotate |
| `env_file_not_ignored` / `env_file_tracked` | medium | An env file with no detected secret is committable or committed | Ignore `.env*`, keep only `.env.example` |
| `no_gitignore` | medium | Env files exist and there is no `.gitignore` at the repo root | Create one |
| `source_secret` | critical in client-side files (public, www, static, client, frontend, web, pages, components, assets, lib, mobile folders; html, vue, svelte, jsx, tsx, dart, swift, kt), high in server code, medium in test files | A privileged-key pattern (a JWT with role service_role, a secret-key format, a cloud access key id, a private key block, a live payment key, a service-account JSON, a database URL with a real-looking password) or a secret-named assignment with a literal | Remove, move to server env, rotate. Check whether the file ships to users |

Detected key shapes are formats, so unknown vendor formats are not detected unless the variable name says secret, private key, password, service role, admin key or token.

## Rules and policies

| Category | Default severity | Meaning | What to do |
|---|---|---|---|
| `rules_open` | critical for write-type, medium for read-only | A rule, JSON rule or permission allows everyone: unconditional allow, `if true`, `.write: true`, `create("any")`-style permission (verify permission syntax against vendor docs, unconfirmed) | Require an owner or role test. Public reads may stay if intended; say so |
| `rules_time_bounded_open` | high | Open until a date (test-mode rule) | Replace now; the app also breaks on that date |
| `rules_auth_only` | medium | Any signed-in user passes, including anonymous sessions | Compare the caller id with the owner field or a role claim |
| `rules_file_missing` | high | `firebase.json` points at a rules file that is not in the folder | Add it or fix the path before deploying |
| `rules_not_configured` | medium | A rules-bearing section has no rules file; the default may be open or closed (verify, unconfirmed) | Commit explicit rules |
| `rules_file_no_allow`, `rules_unparsable` | info, low | Deny-all file; JSON that could not be read | Confirm; fix the JSON |
| `table_without_rls` | high | A public-schema table is created and no SQL file enables row-level security for it | Enable it in the same migration and add policies. The check is across all SQL files; a dashboard-only change is invisible |
| `rls_without_policy` | low | Row-level security on, no policy: only the privileged key can read | Fine for server-only tables; otherwise add policies |
| `policy_open` | high (medium for select) | A policy whose condition is always true; the detail says whether it applies to anonymous callers | Compare the row owner or tenant with the caller |
| `grant_to_anon` | high | A write-capable grant to the anonymous role | Grant select at most, and only with a policy limiting rows |
| `definer_no_search_path` | medium | A function running with its owner's rights and no pinned search path nearby (approximate window check) | Set an empty search path and qualify names |
| `public_bucket` | low | A storage bucket is public in config (verify against vendor docs, unconfirmed) | Keep only intentional public assets there |
| `no_policy_files_found` | info | A backend folder exists with no tables or policies in SQL | Export policies to migrations so they can be reviewed |

## Environment consistency

| Category | Default severity | Meaning | What to do |
|---|---|---|---|
| `env_key_drift` | medium | A key name exists in some of dev, staging and prod (counting the base `.env` and the example file) but not in all | Add it everywhere with that environment's own value, or remove it |
| `env_value_shared_with_prod` | high | A dev, staging or test file has the same value as production for a key or URL variable | Separate project and keys per environment |
| `env_prod_points_to_local` | high | A production URL, host, origin or endpoint value is a local address | Set the real production address |

The script compares only `.env`, `.env.<name>` and `<name>.env` files in one folder, with names development or dev, staging or stage or preview or qa, production or prod, and test. Files named local are not compared (they legitimately differ).
