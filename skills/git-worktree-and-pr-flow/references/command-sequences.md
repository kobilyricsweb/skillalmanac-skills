# Command sequences for the less common cases

Read the section that matches the situation. Each block assumes the primary checkout is clean and on the trunk, and that `origin/main` is the trunk (replace if not).

## Split a big branch

Use when `git diff --shortstat origin/main...HEAD` is over the hard stop. The big branch `feat/big` is kept untouched as the source; new branches take paths from it.

```bash
git fetch origin
git worktree add --no-track -b refactor/big-part1-moves ../repo.wt/big-part1 origin/main
cd ../repo.wt/big-part1
git restore --source=feat/big --staged --worktree -- src/moved/ src/renamed.ts
git diff --cached --stat        # must show only the files you meant
git commit -m "refactor(core): move parsing helpers into src/moved"
```

Order of the pieces: (1) mechanical moves, renames and formatting with no behaviour change; (2) the behaviour change with its tests; (3) follow-ups such as docs and cleanup. Tests travel with the behaviour they cover, never alone in a later PR. Each piece must build and pass tests by itself; run the project's test command in that worktree before pushing. When parts depend on each other, base part 2 on part 1's branch and open it as a draft, retargeting to the trunk after part 1 merges (see Stacked PRs).

Finish: the last piece should leave `git diff feat/big feat/big-partN` empty once all parts are applied; check it, then retire `feat/big`.

## Stacked PRs

```bash
git worktree add --no-track -b feat/child ../repo.wt/child feat/parent
# ... work, push, open the PR against feat/parent as a draft
```

When the parent was squash-merged, its commits no longer exist on the trunk, so a plain rebase replays them and conflicts. Cut them off explicitly:

```bash
git fetch origin
git rebase --onto origin/main <old-parent-tip> feat/child
git push --force-with-lease=feat/child:<old-child-tip>
```

`<old-parent-tip>` is the commit the parent branch pointed to before it merged; read it from `git reflog show feat/parent` or the PR's last commit before merging. Then change the PR's base to the trunk.

## Recover from a mistake

All of these work only for committed work. Uncommitted changes lost to `reset --hard` or `checkout .` cannot be recovered by git.

| Mistake | Recovery |
|---|---|
| `reset --hard` moved a branch | `git reflog show <branch>`, then `git branch rescue/<name> <sha>` |
| Rebase went wrong, not finished | `git rebase --abort` |
| Rebase finished but result is wrong | `git reflog`, find the entry just before `rebase (start)`, `git branch rescue/pre-rebase <sha>` |
| Deleted a branch | `git reflog` for the last commit on it, or `git branch rescue/<name> <sha>` from the PR page's last commit |
| Unpushed commits landed on `main` | `git switch -c feat/right` (new branch at the current tip carries the commits), then `git branch -f main origin/main` (moves `main` without touching files, since it is no longer checked out) |
| Pushed a secret | rotate the secret first; history rewriting is a separate, owner-approved step |

Always create the `rescue/` branch before experimenting further; it costs nothing and a later `git branch -d` removes it.

## Cleaning many old branches

1. Run the audit script; list `upstream_gone`, `stale_branch` and `no_upstream` subjects.
2. For each, check merge status from the hosting service or `git branch -r --merged origin/main`; the script cannot.
3. Present the list with the reason per branch to the user. Delete only the ones the user confirms, with `git branch -d`, or `-D` only after confirming a squash-merged PR.
4. Run `git worktree prune` and `git fetch --prune origin`, then the audit again.

## Per-task environment in a worktree

A new worktree has only tracked files. Before starting: install dependencies, copy `.env.example` to `.env` and fill it from the user's instructions (never from another worktree's secrets without being told), choose a port that no other worktree uses (for example base port plus the worktree's index), and set a distinct database name or schema when tests write data. Two agents sharing one dev database in two worktrees is the most common cause of mysterious test failures in parallel work.
