# Listing page content: git-worktree-and-pr-flow

**One line:** Runs parallel agent tasks in isolated git worktrees with clean branches, small PRs and a safe merge flow.

## What it does

The skill fixes one rule (one task, one worktree, one branch, one PR) and supplies the exact commands for it: creating a worktree with `--no-track` from a fresh remote trunk, working in small commits, syncing by a rebase-or-merge decision table, checking PR size against numeric limits (400 changed lines and 15 files as target; 800 and 25 as hard stop), and cleaning up in the right order. It defines a branch naming contract and a commit message contract, and lists the commands an agent must never run with the safe alternative for each. A bundled script reads `.git` files (refs, `packed-refs`, config, reflogs, `worktrees/`) without running git and prints a JSON report of stale worktrees, branches with no upstream, naming violations and other hazards.

## Capabilities

- `scripts/repo_branch_audit.py`: JSON report with 15 finding codes (stale or idle worktrees, detached HEAD, missing upstream, vanished upstream, naming violations, stale branches, operations in progress, stale lock files)
- Command sequences for creating, syncing, splitting, stacking and removing, with recovery recipes
- A never-run table covering force push, `reset --hard`, `clean -fdx`, forced worktree removal and shared-stash traps
- A fixed report format

## When to use

You say git worktree, parallel agents, several tasks at once, branch naming, rebase or merge, PR too big, split this PR, or clean up old branches and worktrees.

## When not to use

Reviewing the content of a diff (use a code-review skill), resolving conflict contents, setting up CI, tagging releases. Difference from `reviewing-code-changes`: that skill judges whether a change is correct and safe; this one manages the lifecycle of the branch that carries the change.

## Requirements

Python 3.9 or newer for the script (standard library only, no network, no subprocess, never runs git). Without Python the agent uses the listed manual git commands.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so no saved agent answer is shown. What exists is the script on the saved fixtures (`python evals/run_fixtures.py`, 7/7 pass):

1. Fixture repo with five worktrees and seven branches, audited with a fixed clock: `ok` false, counts 1 error, 13 warn, 2 info. Examples of findings: `error stale_worktree gone-task` (checkout directory gone, `git worktree prune`), `warn idle_worktree alive-task` (HEAD has not moved for 20.0 days, limit 14), `warn naming_violation Feature/NewThing` (contains uppercase; type not allowed), `warn upstream_gone fix/old-bug`, `warn stale_lock (primary)` (index.lock is 60 minutes old). Exit code 1.
2. Fixture repo with `main` and `feat/add-search` plus one linked worktree: `ok` true, no findings, exit code 0, also when run from inside the linked worktree.

## Limits

- Reads metadata only: no uncommitted changes, no commit contents, no merge status.
- Reftable repositories are reported, not read.
- Size limits are working values, not measured optima.
- Submodules, sparse checkouts and bare repositories are not covered.

## Evidence

See `VERIFICATION.md`. Static lint 0 FAIL / 0 WARN; 7 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool install, human review, run against a real repository.

## Demo script (60 to 90 seconds)

To be recorded from a real run. Planned beats:

1. User asks for three parallel tasks; the agent runs the audit (clean), then three `git worktree add --no-track` commands with contract-conforming names.
2. One task grows; the agent measures `--shortstat`, sees it over the hard stop and splits with `git restore --source`.
3. A colleague has pushed to the branch; the agent merges the trunk instead of rebasing and refuses to force-push.
4. After merge: remove worktree, delete branch, prune; audit again shows 0 findings.

## FAQ seeds

- Does it need network access? No. The script reads local files only.
- Does the script run git? No; it parses `.git` files, which is why it cannot see merge status.
- Does it work on Windows? The script is written to, and was run on Windows 11; macOS and Linux are untested.
- Can I change the naming types or limits? Yes: `--types`, `--trunk`, `--stale-worktree-days`, `--stale-branch-days`.
- How is it different from a code review skill? It does not read the diff for defects; it manages branches, worktrees, PR size and merge order.
- Will it merge or delete things for me? Merging is left to the user; deletions need confirmation because merge status is not visible to the script.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
