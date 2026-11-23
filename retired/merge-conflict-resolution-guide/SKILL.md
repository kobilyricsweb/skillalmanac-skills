---
name: merge-conflict-resolution-guide
description: Resolves a git merge conflict hunk by hunk by classifying each conflict block, applying a fixed decision table per class, and running post-resolution checks before handing back. Use when a merge, rebase or cherry-pick stops with unmerged paths and each conflict must be resolved with a stated reason rather than by taking one side. Do not use for creating conflict-free merge commits, choosing a branching strategy, or resolving conflicts in binary files.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B), with git available on the command line for the commands below.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Merge Conflict Resolution Guide

Resolve each conflicted hunk on its own evidence. Never take ours or theirs for a whole file. Every hunk gets one class, one decision, one reason, and is covered by a check. The license text is in LICENSE.txt in this folder. This package has no scripts and no evals.

## Workflow

### Step 1: Confirm the merge state
1. Run `git status` and confirm there are unmerged paths.
2. Identify the operation and its refs, then record the three commits:
   - merge: theirs = `MERGE_HEAD`; base = `git merge-base HEAD MERGE_HEAD`.
   - rebase: theirs = `REBASE_HEAD` (the commit being replayed); base = `git rev-parse REBASE_HEAD^` (its parent, not a merge-base).
   - cherry-pick: theirs = `CHERRY_PICK_HEAD` (the picked commit); base = `git rev-parse CHERRY_PICK_HEAD^`.
   - ours is `git rev-parse HEAD` in all three cases.
3. Check which ref exists: `MERGE_HEAD` means merge, otherwise `REBASE_HEAD` means rebase, otherwise `CHERRY_PICK_HEAD` means cherry-pick. Record the operation name.
4. If none of those refs exist, stop (see Refuse / stop when).
5. Side meaning: in a merge, "ours" is your current branch and "theirs" is the branch being merged in. In a rebase, the meaning is reversed for your own work: "ours" is the base you are rebasing onto (HEAD), and "theirs" is the commit being replayed, which is your change. Cherry-pick labels follow the rebase pattern: "ours" is HEAD and "theirs" is the picked commit. Every intent sentence and every "ours" or "theirs" label in the output must name the commit it refers to, not just the marker word.

Output: the three SHAs, the operation name, the side meaning used, and the list of unmerged paths.

### Step 2: Capture the intent of each side
1. For each unmerged file, run `git log --oneline <base>..HEAD -- <file>` and `git log --oneline <base>..<theirs> -- <file>` (<theirs> is the ref you recorded in step 2: MERGE_HEAD, REBASE_HEAD or CHERRY_PICK_HEAD).
2. Read the commit subjects. Write one sentence per side saying what that branch was trying to do with this file.
3. If the subjects are empty or vague, read `git diff <base> HEAD -- <file>` and `git diff <base> <theirs> -- <file>`. Write the sentence from the code and label it "inferred".

Output per file: `intent_ours` and `intent_theirs`, each marked "stated" or "inferred".

### Step 3: Split the file into hunks
1. Before any edit, run `git checkout --conflict=diff3 -- <file>`. This recreates the markers with the base text visible. It discards any manual edits made to that file since the conflict started, so do it first.
2. Each block from `<<<<<<<` to `>>>>>>>` is one hunk. Label them H1, H2, and so on in file order.
3. If either side of a hunk is longer than 40 lines, split it at blank lines or function boundaries into sub-hunks (H3a, H3b).

Output: a table with columns id, file, start line, ours line count, theirs line count.

### Step 4: Classify each hunk
Use this table. If a hunk fits two classes, use the class that comes later in the table.

| Class | Signal | Default action |
|---|---|---|
| A. Independent | Changed lines do not overlap in base and the intents do not interact | Keep both changes, ordered by dependency |
| B. Same change | Both sides produce identical behavior | Keep one; prefer the side that has tests |
| C. Conflicting intent | Same lines or same expression with different results | Write one version that meets both intents; if that needs a product decision, hand back |
| D. Moved code | One side moved or renamed code the other side edited | Apply the edit at the new location; confirm the move with `git log --follow` or `git diff -M` |
| E. Delete vs modify | One side deleted a block the other side changed | Count references with a search. Zero references: accept the delete. One or more: keep the modified version and update each reference |
| F. Generated or lockfile | Path is a lockfile or a generated output | Never hand-merge. Take either side, regenerate with the project's own command, then confirm the regenerated file |

### Step 5: Resolve each hunk
1. Work on one hunk at a time. For each hunk, write the chosen text as a replacement for the whole block: from the `<<<<<<<` line through the `>>>>>>>` line, markers included. The markers are removed, and the chosen text takes their place. Do not write candidate versions to other files or to a copy. Lines outside the blocks stay byte-identical.
2. Apply the class default from Step 4 unless a Step 5 threshold says otherwise.
3. Thresholds (working values, not industry standards):
   - Class C: resolve only if at least one test or a direct call-site read covers the changed function. Otherwise hand back.
   - Class E: more than 5 references means hand back, not a mechanical fix.
   - Any hunk you cannot explain in one sentence after two careful readings: hand back.

### Step 6: Record each decision
Write one row per hunk: id, class, decision, reason. The reason must cite the intent sentence from Step 2 that supports the decision.

### Step 7: Verify before staging
Run these checks in order. Stop at the first failure and report it.

1. No markers: search each resolved file for lines starting with `<<<<<<<`, `=======`, or `>>>>>>>`. Expected: zero matches.
2. Whitespace: `git diff --check`. Expected: no output.
3. Build or type check: prefer the project's own command (ask the user for it if the repository does not show one). Defaults when the files show no other command:
   - Node/TypeScript: `npm run build` if defined, and `node_modules/.bin/tsc --noEmit` (the project's own installed TypeScript) when a `tsconfig.json` exists.
   - Python: `python -I -m compileall -q <touched dirs>` for syntax, plus the project's type checker if configured.
   - Go: `go build ./...`. Rust: `cargo check`. Java with Maven: `mvn -q -DskipTests compile`.
   - Any other language: ask the user for the command before running Step 7.
   Expected: exit code 0.
4. Tests for touched functions: expected all pass. Use the project's test command (for example `npm test`, `python -m pytest <touched test files>` (no -I here: isolated mode cannot import project modules from the working directory), `go test ./<touched pkg>`). Record the count run.
5. Both parents: `git diff HEAD -- <file>` must show every theirs change you kept. `git diff MERGE_HEAD -- <file>` must show every ours change you kept. In a rebase or cherry-pick, use `REBASE_HEAD` or `CHERRY_PICK_HEAD` in place of `MERGE_HEAD`. A hunk that appears in neither diff was silently dropped; restore it or justify it in Step 6.
6. Do not stage in this step. Staging is a change to the index that the user did not ask for. Report the list of resolved files in the Checks table, and run `git add <file>` for each only when the user asks, or after the user has reviewed the hunk table.

### Step 8: Hand back
Write the output contract below. Do not commit unless the user asks.

## Output contract

Use these headings, in this order, with these table columns.

## Merge state
- ours: <sha>
- theirs: <sha>
- base: <sha>
- operation: merge | rebase | cherry-pick

## Hunk decisions
| Hunk | File | Class | Decision | Reason |
|---|---|---|---|---|

## Checks
| # | Check | Result |
|---|---|---|

## Hand back
A bulleted list. Each item names the hunk id and the one decision needed from the user. Write "none" if the list is empty.

## Refuse / stop when
- The user asks to take ours or theirs for a whole file without hunk review. Explain that the hunk table is required and offer to produce it.
- Neither `MERGE_HEAD`, `REBASE_HEAD`, nor `CHERRY_PICK_HEAD` exists.
- Unrelated uncommitted changes exist in the working tree. Ask the user to commit or stash them first.
- A lockfile or generated file was hand-edited. Discard the hand edit and regenerate.
- A conflict is in a binary file. Hand back; never pick a side silently.
- A class C hunk has no test and no call-site coverage.
- The user asks to force-push, reset history, or rewrite published commits as part of the resolution.
- The build or tests fail and the cause is not inside a resolved hunk.
- Any check in Step 7 fails and the cause is unknown after one read of the failing output.
