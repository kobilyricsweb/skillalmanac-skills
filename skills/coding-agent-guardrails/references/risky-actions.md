# Risky actions: safe forms and detection

Read the section that matches the action. Nothing here needs the network.

## Contents

- Git commands that destroy work
- Safer alternatives
- Generated and vendored files
- Tests: ways of cheating that look like fixes
- Secrets: names and value patterns

## Git commands that destroy work

| Command | What is lost | Ask first |
|---|---|---|
| `git reset --hard` | uncommitted changes in tracked files | yes |
| `git clean -f`, `-fd`, `-fdx` | untracked files (and ignored ones with `-x`) | yes |
| `git checkout -- <path>`, `git checkout .`, `git restore <path>` | uncommitted edits to those paths | yes |
| `git stash drop`, `git stash clear` | stashed work | yes |
| `git branch -D`, `git push origin --delete` | unmerged commits, remote branch | yes |
| `git push --force`, `-f`, `+branch` refspec | other people's commits on the remote | yes, every time |
| `git rebase`, `git commit --amend` on pushed commits | rewrites shared history | yes |
| `git reflog expire`, `git gc --prune=now` | the recovery path itself | never without an explicit request |

The same destructive effect hides in other spellings: flags after the branch name, combined flags, aliases, and `git -C <dir>` forms. Judge by the effect, not the exact string.

## Safer alternatives

- Instead of `reset --hard`: `git stash push -u` (keeps untracked files too), or create a branch at the current commit first.
- Instead of `clean -fd`: `git clean -nd` to list, show the list, then ask.
- Instead of `push --force`: ask; if a forced push is approved, use `--force-with-lease` with the expected ref.
- Instead of deleting a failing branch: leave it and report.
- Commit or push only when the user asked for it in this session.

## Generated and vendored files

Signs a file is not meant to be hand-edited: a first-lines marker (`DO NOT EDIT`, `@generated`, `auto-generated`), a path under `dist`, `build`, `out`, `generated`, `vendor`, `third_party`, `.next`, a `.min.` name, a lockfile, protobuf or ORM output (`*.pb.go`, `*_pb2.py`), a database migration that has already been applied, a `linguist-generated` line in `.gitattributes`.

Procedure: find the generator or the source (look for the marker text, a `codegen` or `generate` script, a template), change that, run the generator, and show the diff of the output. For vendored code: change the project's own code to work around it, or ask about upgrading the vendored copy.

## Tests: ways of cheating that look like fixes

Treat each of these as a change to the test suite that needs the user's approval: deleting a test; `skip`, `xit`, `@Ignore`, `pytest.mark.skip`, `xfail`; commenting out an assertion; weakening an equality to a truthiness check; widening a numeric tolerance; adding a sleep or a retry to hide a flake; catching the exception inside the test; updating a snapshot without reading the diff; lowering a coverage threshold; excluding a path from the test run.

Legitimate: fixing a test that is wrong, with the reason stated and the user informed.

## Secrets: names and value patterns

Names: `.env`, `.env.*` (but `.env.example` is fine), `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `credentials.json`, `service-account*.json`, `.npmrc` with a token, `.netrc`.

Value shapes: `AKIA` followed by 16 characters (cloud access key id), `ghp_` or `github_pat_` (repo tokens), `sk-` (API keys), a private-key block header, a `password=` or `token=` assignment with a literal value, a long mixed-case string assigned to a variable named secret, key or token.

If one is found in a staged file: unstage it, tell the user which file and line number (not the value), and suggest rotating it if it was ever pushed.
