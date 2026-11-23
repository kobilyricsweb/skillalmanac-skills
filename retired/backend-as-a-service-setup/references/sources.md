# Sources

The package was authored without fetching these pages. Vendor-specific statements in the skill are marked "verify against vendor docs (unconfirmed)". Open the matching page before relying on one. Summaries are in the author's own words.

| Topic | Page | What to confirm there |
|---|---|---|
| Row-level security in a Postgres-based BaaS | https://supabase.com/docs/guides/database/postgres/row-level-security | Which key bypasses policies; how a policy reads the caller id; whether views honour policies; which user fields a user can edit |
| Postgres policy syntax | https://www.postgresql.org/docs/current/sql-createpolicy.html | USING versus WITH CHECK; default of applying to all roles |
| Document-database security rules | https://firebase.google.com/docs/rules | Rules are not filters; limits on document reads inside a rule; default behaviour when no rules file is deployed |
| Realtime-database rules | https://firebase.google.com/docs/database/security | Cascading of read and write; rule expression syntax |
| Open-source BaaS permissions | https://appwrite.io/docs/advanced/platform/permissions | Permission string syntax and the meaning of the any role |
| Password guidance | https://pages.nist.gov/800-63-4/sp800-63b.html | Minimum length and breached-password screening |
| Secret scanning and leaks | https://docs.github.com/en/code-security/secret-scanning | What providers do when a key is pushed |
| Mobile login-service rules | https://developer.apple.com/app-store/review/guidelines/ | The sign-in-with requirement and its exceptions |
