# Git facts this skill relies on

Each fact is stated in our own words with the official page that documents it. Read this when a user or reviewer challenges a rule in `SKILL.md`, or before changing the audit script.

## Contents

- Worktrees
- Tracking and pushing
- Branch names
- Refs and files the script reads
- Recovery window

## Worktrees

- A linked worktree is a second working directory attached to the same repository; objects, branches, tags, config and hooks are shared, while HEAD, the index and some state are per worktree. Source: https://git-scm.com/docs/git-worktree
- A branch can be checked out in only one worktree at a time unless forced. Same page.
- `git worktree remove` refuses a worktree with modified or untracked files unless forced, and refuses a locked one. `git worktree prune` deletes the administrative record of a worktree whose directory is gone, unless it is locked. Same page.
- The page states that multiple checkout is still experimental and that submodule support is incomplete; this is why the skill warns before using worktrees in a repo with submodules. Same page.
- The stash is stored in a shared ref (`refs/stash`), so every worktree sees the same stash list. Source for ref layout: https://git-scm.com/docs/gitrepository-layout

## Tracking and pushing

- When a new branch starts from a remote-tracking branch, git sets that branch as its upstream by default (`branch.autoSetupMerge`). `--no-track` turns that off for one command. Sources: https://git-scm.com/docs/git-branch and https://git-scm.com/docs/git-config
- With `push.default` at its default `simple`, a plain `git push` to a differently named upstream is refused; a same-name upstream works. Source: https://git-scm.com/docs/git-config
- `--force-with-lease` refuses to overwrite a remote ref that is not where you expected. Given as `--force-with-lease=<ref>:<sha>` it names the expected value explicitly, which is safer than relying on the remote-tracking ref that a background fetch may have refreshed. Source: https://git-scm.com/docs/git-push

## Branch names

- A branch named `feat` cannot coexist with `feat/x`, because refs are stored as files and directories. This is why every branch has a type prefix and nothing is named only `feat`. Rules for valid ref names (no `..`, no trailing `.lock`, no trailing slash or dot, no spaces) are in https://git-scm.com/docs/git-check-ref-format

## Refs and files the script reads

- Loose branch refs are files under `refs/heads/`, each holding a full object id; `git pack-refs` moves many into the single `packed-refs` file, one `<id> <refname>` per line, with lines starting `#` or `^` being a header or a peeled tag id. Sources: https://git-scm.com/docs/git-pack-refs and https://git-scm.com/docs/gitrepository-layout
- Branch tracking is configuration: a `[branch "<name>"]` section with `remote` and `merge`. Source: https://git-scm.com/docs/git-config
- Per-worktree administrative data lives under `<common dir>/worktrees/<id>/`: `gitdir` (path of the worktree's `.git` file), `HEAD`, `locked`, and `commondir` in linked worktrees. The `gitdir` path may be relative when the repository is configured for relative worktree paths. Sources: https://git-scm.com/docs/gitrepository-layout and https://git-scm.com/docs/git-worktree
- A linked worktree's `.git` is a file whose single line starts `gitdir:`. Same sources.
- Reflog lines are `<old id> <new id> <name> <email> <epoch> <timezone><TAB><message>`, kept under `logs/`. Source: https://git-scm.com/docs/git-reflog
- The reftable backend stores refs in tables, not loose files. Source: https://git-scm.com/docs/reftable

## Recovery window

- Reflog entries expire after 90 days by default, and entries for commits no longer reachable from the branch after 30 days (`gc.reflogExpire`, `gc.reflogExpireUnreachable`). Uncommitted changes are never in the reflog. Source: https://git-scm.com/docs/git-gc and https://git-scm.com/docs/git-config
