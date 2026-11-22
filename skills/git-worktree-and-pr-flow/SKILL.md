---
name: git-worktree-and-pr-flow
description: Git worktree and PR flow for parallel agents. Use when the user says git worktree, parallel agents, several tasks at once, branch naming, rebase or merge, PR too big, split this PR, or clean up old branches or worktrees. Gives exact worktree add and remove sequences, a branch naming contract, a rebase-or-merge table, PR size limits, a commit message contract, a never-run list, and a read-only script that reads .git files without running git to report stale worktrees, branches with no upstream and naming violations as JSON. Do not use for reviewing a diff, resolving conflict contents, CI setup or release tagging.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer, standard library only. It reads files and never runs git or uses the network. Without Python, use the manual commands in step 2 of the workflow.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Git worktree and PR flow

One task gets one worktree, one branch and one PR. The primary checkout stays on the trunk, clean, and nobody edits in it. Everything below keeps that true when several agents work at once.

## Contracts at a glance

| Item | Contract |
|---|---|
| Branch name | `<type>/<slug>`; type is one of feat fix chore docs refactor test perf ci build hotfix release; slug lowercase kebab, up to 40 characters; whole name up to 50 |
| Worktree path | sibling of the repo, never inside it: `../<repo>.wt/<slug>` |
| PR size target | up to 400 changed lines and 15 files, one concern |
| PR size hard stop | over 800 changed lines or over 25 files: split before asking for review |
| Active agent worktrees | up to 4 per human reviewer |
| Commit subject | `<type>(<scope>): <imperative summary>`, up to 72 characters, no final period |
| Force push | only `--force-with-lease=<branch>:<sha>` on your own unshared feature branch |

Changed lines means added plus deleted from `git diff --shortstat origin/main...HEAD`, minus lockfiles, generated code, snapshots and pure renames. The limits are house working values, not measured optima; a PR that must exceed them says why in its description.

## Workflow

```
- [ ] 1 Audit the repo (script)
- [ ] 2 Create the worktree
- [ ] 3 Work in small commits
- [ ] 4 Sync with the trunk (decision table)
- [ ] 5 Size check and split if needed
- [ ] 6 Publish and open the PR
- [ ] 7 After merge, clean up
- [ ] 8 Report
```

1. **Audit.** `python scripts/repo_branch_audit.py <repo>`. Read the `findings`; fix `error` first. Run it again at step 7. Without Python, run `git worktree list --porcelain`, `git branch -vv` and `git status --short` and read them the same way.
2. **Create.** Always branch from a fresh remote trunk, and always pass `--no-track`:

```bash
git fetch origin
git worktree add --no-track -b feat/add-search ../repo.wt/add-search origin/main
cd ../repo.wt/add-search
git push -u origin HEAD        # first push sets the upstream under the same name
```

   Without `--no-track`, a branch started from `origin/main` tracks `origin/main`, and the default `push.default=simple` then refuses to push it. Install dependencies and copy untracked config inside the new worktree; `node_modules`, virtual environments and `.env` are not shared. A branch can be checked out in only one worktree at a time. Submodules in linked worktrees are poorly supported: if the repo has submodules, tell the user before using worktrees.
3. **Work.** Commit by explicit path (`git add path/to/file`), never `git add -A`; check `git diff --cached --stat` before every commit. One logical change per commit, and every commit builds. Follow the commit contract below.
4. **Sync.** Pick the row that matches, from the table in the next section. Run `git fetch origin` first.
5. **Size.** `git diff --shortstat origin/main...HEAD` and `git log --oneline origin/main..HEAD`. Above the hard stop, split: see [references/command-sequences.md](references/command-sequences.md), section Split a big branch.
6. **Publish.** `git push` (plain, or with lease after a rebase). PR title uses the commit subject format, because a squash merge uses it as the commit message. PR body has five headings: Why, What changed, How tested, Risk and rollback, Out of scope. Merge only when the user says so; do not push to the trunk.
7. **Clean up** after the PR merged, in this order:

```bash
cd <primary checkout>
git fetch --prune origin
git worktree remove ../repo.wt/add-search     # refuses if the tree is dirty; do not add --force
git branch -d feat/add-search                 # fails after a squash merge, see below
git worktree prune
```

   After a squash or rebase merge `git branch -d` says "not fully merged" because the commits differ. Confirm the PR is merged and the remote branch was deleted, then use `git branch -D`. If the PR is not merged, do not delete.
8. **Report** in the fixed format at the end.

## Rebase or merge: decision table

| Situation | Do | Command |
|---|---|---|
| Local branch, never pushed, behind trunk | rebase | `git rebase origin/main` |
| Pushed, only you commit to it, no other branch built on it | rebase, then lease-push | `git rebase origin/main && git push --force-with-lease=feat/x:<old-sha>` |
| Someone else pushed to it, or another worktree branches from it | merge the trunk in, no rewrite | `git merge origin/main` |
| Stacked: child branch, parent was squash-merged | transplant the child | `git rebase --onto origin/main <old-parent-tip> feat/child` |
| Rebase conflicts again on most of 10 or more commits | abort, squash, retry | `git rebase --abort`, then `git reset --soft $(git merge-base HEAD origin/main)`, commit once, rebase |
| Long-lived release branch needs trunk fixes | merge | `git merge origin/main` |
| Landing the PR | follow the repo's setting; default squash. Rebase-merge only if every commit is atomic and builds. Merge commit only for a long branch with several authors | the hosting service's merge button, on the user's say-so |

Record the pre-rebase tip first (`git rev-parse HEAD`); it is the `<old-sha>` in the lease and the way back. A lease-push that is rejected means someone else pushed: stop, fetch, look at `git log origin/feat/x`, and ask. Never retry with `--force`.

## Commit message contract

```
<type>(<scope>): <imperative summary, up to 72 chars>

<why, wrapped at 72 characters: the problem and the reason for this approach>

Refs: #123
Co-Authored-By: <the agent's trailer if the project uses one>
```

Types are the branch types plus `revert`. Breaking changes add a `BREAKING CHANGE:` footer. Review fixes never stay as "address comments" commits: create them with `git commit --fixup=<sha>` and fold them before the final push with `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash origin/main` (the empty editor makes it non-interactive).

## Never run

| Command | Why it is dangerous | Do instead |
|---|---|---|
| `git push --force` or `-f` | overwrites other people's commits; on `main` or `release/*` it rewrites history everyone has | lease-push on your own branch only; on shared branches, add a revert commit |
| `git reset --hard` on a tree with changes, or with the tip not noted | uncommitted work is gone for good; reflog only saves committed work | `git status --porcelain` must be empty and `git rev-parse HEAD` saved; otherwise `git stash push -u -m <task>` or a WIP commit |
| `git clean -fdx` or `-x` | deletes ignored files: `.env`, local databases, `node_modules` | `git clean -nd` first, never `-x` |
| `git checkout .`, `git restore .` | discards every unstaged edit at once | restore named paths only |
| `git worktree remove --force` | deletes a dirty or locked worktree without asking | `git -C <path> status --short` first |
| deleting `.git/worktrees/*` by hand | leaves dangling metadata or breaks live worktrees | `git worktree remove`, then `git worktree prune` |
| `git branch -D` on an unmerged branch with no remote copy | the only copy lives in the reflog | push it, or confirm the merged PR |
| `git commit --amend`, `git rebase` on commits others have pulled | their next pull conflicts | add a new commit |
| `git reflog expire --expire=now --all`, `git gc --prune=now` | removes the recovery net | leave gc to git |
| `--no-verify` | skips the project's hooks | only when the user asks, and say so in the report |
| `git push origin main` | bypasses review | open a PR |

`git stash` is shared by all worktrees of a repository, so an agent in another worktree can pop yours. Prefer a WIP commit; if you stash, always use `-m <task>` and pop by that message.

## The audit script

`python scripts/repo_branch_audit.py <repo-or-git-dir> [--stale-worktree-days 14] [--stale-branch-days 30] [--types a,b] [--trunk a,b]` reads `.git` files only and never runs git. Run it; do not edit it to make a finding go away. It accepts a work tree root, a linked worktree root or a git directory.

Output is one JSON object:

```
{"tool","schema_version":1,"git_dir","common_dir","policy":{...},"now",
 "worktrees":[{"id","path","exists","head_kind","head","locked","lock_reason","age_days"}],
 "branches":[{"name","source","sha","upstream","upstream_ref_exists","age_days","checked_out_in"}],
 "remote_branch_count","findings":[{"severity","code","subject","detail"}],
 "counts":{"error","warn","info"},"ok","not_checked":[...]}
```

Exit 0 when there is no error or warn finding, 1 otherwise, 2 for a usage error or a path that is not a repository. Finding codes, and the fix each one points to:

| Code | Severity | Meaning | Fix |
|---|---|---|---|
| `stale_worktree` | error | checkout directory is gone, record remains | `git worktree prune` |
| `worktree_metadata_broken` | error | `gitdir` file missing or empty | inspect by hand, then prune |
| `invalid_ref_file` | error | a ref file is not a hex id | do not touch; ask the user |
| `locked_worktree_missing` | warn | locked and directory gone | `git worktree unlock`, then prune, if the disk is not just unplugged |
| `idle_worktree` | warn | HEAD has not moved for over 14 days | ask whether to finish or remove it |
| `detached_worktree` | warn | HEAD on no branch | create a branch before committing more |
| `worktree_branch_missing` | warn | HEAD names a branch that does not exist | recreate or switch |
| `naming_violation` | warn | name breaks the contract; the detail lists each reason | rename with `git branch -m` after checking nobody uses it |
| `no_upstream` | warn after 3 days, else info | never pushed or tracking not set | `git push -u origin HEAD` |
| `upstream_gone` | warn | tracked remote branch no longer exists | merged and deleted: confirm, then remove; otherwise re-push |
| `stale_branch` | warn | last update over 30 days ago | rebase, finish or delete after confirming |
| `operation_in_progress` | warn | rebase, merge, cherry-pick, revert or bisect marker present | finish or abort it |
| `reftable_unsupported` | warn | reftable ref storage, refs are not readable from files | use git commands |
| `stale_lock` | warn | a `.lock` file older than 10 minutes | remove only after confirming no git process runs |

Ages come from reflog timestamps, falling back to file modification time. A packed branch with no reflog has no age. The script cannot tell whether a branch is merged: check that with `git branch -r --merged origin/main` or the hosting service before deleting anything.

## Report

```
Worktrees: <created, removed, still open, with paths>
Branches: <names, upstream state, naming result>
Sync: <rebase or merge, which table row, old and new tip>
PR size: <lines, files, commits; split or not>
Audit: <counts error/warn/info before and after>
Not done: <merge, deletions left for the user, anything not verified>
```

## Limits

- The script reads only metadata. It does not see uncommitted changes, commit contents, message format or merge status.
- Reftable repositories (`extensions.refStorage = reftable`) have no loose refs or `packed-refs`; the script then reports no branches. Use the manual commands.
- The size and count limits are working values from this skill, not studies. Adjust to the team's review capacity.
- Worktree behaviour with submodules, sparse checkouts and bare repositories is not covered.
- The worktree path contract (`../<repo>.wt/<slug>`) is guidance only; the script does not enforce it.
- It does not review code; for that use a review skill.

Read [references/git-facts.md](references/git-facts.md) only when a rule here is challenged or before editing the script; it cites the official git page behind each fact.
