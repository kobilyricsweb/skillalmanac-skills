## Contents

- Ground rules
- The 12 tests
- Results table
- Writing the runner

# Smoke-test plan

## Ground rules

- Run against dev, then staging. Never against prod with writes. Use two throwaway users, A and B, created for the test and deleted after.
- The agent writes the test script; the user runs it with keys supplied through environment variables. The agent does not read the keys.
- Each test has an expected outcome. "Denied" means an error status (401, 403) or an empty result with zero rows changed; vendors differ on which they return, and either is a pass. "Rows returned" or "rows changed" for a caller who should not have them is a fail.
- Run the whole list after every change to rules, policies, storage settings or auth settings, and before each production rules deploy.

## The 12 tests

| # | Test | Expected | If it fails |
|---|---|---|---|
| 1 | With only the public key and no user token, read every table and collection | no rows, except tables intended as public | the table has no policy or an open one; fix in step 5 |
| 2 | Same caller inserts a row into every table | denied everywhere | missing insert policy, or an anon grant |
| 3 | A creates a row. B reads it by its id | not visible to B | read policy is too wide (`true`, or signed-in only) |
| 4 | B updates A's row, then B deletes it | zero rows changed both times | update or delete policy missing or wide |
| 5 | A updates their own row and sets the owner column to B's id | denied | update policy lacks the with-check half |
| 6 | A sets their own role, admin flag or tenant id through the normal API | denied, or the value is ignored | privilege fields are writable by the user, or the policy reads a user-editable claim |
| 7 | Anonymous caller requests a private storage object by its path | denied | bucket is public or has an open read policy |
| 8 | A uploads a file under B's path prefix; B downloads A's private file | both denied | storage policy does not compare the path prefix with the caller |
| 9 | Upload a file over the size cap and one with a disallowed type (for example an HTML file renamed to .png) | both rejected | limits are only in the client; set them on the bucket |
| 10 | Request a signed URL, wait past its lifetime plus 10 seconds, request again | second request denied | lifetime is far longer than intended |
| 11 | Auth: register with an email but do not confirm; try to read data. Then send 10 wrong sign-ins in one minute | no data before confirmation; later attempts rate-limited (429 or a lock) | confirmation is off or rate limits are off |
| 12 | Environment: call the prod project with the dev public key, and the dev project with the prod key; check the built client config of each environment | both calls rejected; each build contains only its own project URL | keys or URLs shared across environments |

Two extra checks where the vendor offers them (verify against vendor docs, unconfirmed): subscribing to realtime changes as B should not deliver A's rows; and a redirect to a URL that is not on the allow-list should be refused at sign-in and password reset.

## Results table

Give the user this table filled in, with the tool output path for each row:

```
| # | Environment | Result (pass/fail/not run) | Evidence | Notes |
```

Rows marked not run stay in the report. A smoke test run on dev says nothing about prod settings that were changed in the dashboard by hand.

## Writing the runner

Keep it one file in the user's language, reading `BAAS_URL`, `BAAS_PUBLIC_KEY`, `USER_A_EMAIL`, `USER_A_PASSWORD`, `USER_B_EMAIL`, `USER_B_PASSWORD` from the environment. Print a pass/fail line per test and exit non-zero on any fail so CI can gate on it. Do not log request headers (they carry tokens).
