# Merge Conflict Resolution Guide

## One line
Walks an agent through a stopped git merge, rebase or cherry-pick one conflict hunk at a time, with a fixed class table, a decision per hunk, and checks before anything is staged.

## What it does
The skill starts by confirming that git is really in a conflicted state and records the three commits that matter: ours, theirs, and the merge base. It then reads the commit subjects on each side to state what each branch was trying to do with the file. Next it recreates the conflict markers in diff3 style so the base text is visible, splits the file into numbered hunks, and assigns each hunk one of six classes: independent, same change, conflicting intent, moved code, delete versus modify, and generated or lockfile. Each class has a default action. Resolution edits only the text between markers. Every hunk gets a row that names the class, the decision, and the reason, and the reason must cite a stated intent.

Before staging, the skill runs a fixed check list: no markers left, a whitespace check, the project's own build, tests for the touched functions, and a comparison of the result against both parents so that no hunk is silently dropped. The output is a short contract with a merge state block, a hunk decision table, a checks table, and a hand-back list for anything that needs a human decision.

## When to use
Use it when a merge, rebase or cherry-pick stops with unmerged paths and the conflicts are in source files that have tests or call sites. It fits cases where two branches edited the same function for different reasons, where one branch moved code the other branch changed, or where a deleted block is still referenced somewhere.

## When not to use
Do not use it to prevent conflicts, to choose a branching strategy, or to resolve conflicts in binary files. It does not cover history rewriting, force pushes, or commit signing. A lockfile is regenerated rather than merged, so this skill is not a substitute for the package manager.

## Requirements
Git on the command line and a text-capable agent. There are no scripts, no network calls, and no packages to install. The build and test commands are whatever the project already uses.

## Example
The smoke run used a pasted hunk where two branches changed one function in different ways. The output is an excerpt of the contract, produced by following the SKILL.md steps by hand. See VERIFICATION.md for the full input and the reasoning.

```
## Hunk decisions
| Hunk | File | Class | Decision | Reason |
|---|---|---|---|---|
| H1 | pricing.js | A | Keep both: qty multiplier from ours, shipping term from theirs | Intents do not interact in the subtotal; shipping is added on the return line |

## Hand back
- H1: Confirm whether SHIPPING_FEE should be taxed. The current result adds it after tax.
```

## Limits
The class table is a working guide, and the thresholds (40 lines per hunk, more than 5 references, two careful readings) are working values, not published standards. The skill cannot judge product rules, so any choice that depends on business intent is handed back to the user. It assumes the commit history is readable and that tests exist for the code that changed. A hunk that spans several unrelated functions may need manual splitting.

## Status
Provisional. Lint-clean, one smoke run. Not independently verified.
