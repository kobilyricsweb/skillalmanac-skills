# Worked examples

Each example shows a normal reply and the same content at the three levels.

## How-to: find what is using a port

Normal:

> Sure! To find out which process is using port 3000, you can use the `lsof` command on macOS or Linux. Run `lsof -i :3000` and look at the PID column in the output. Once you have the PID, you can stop the process with `kill <PID>`. If it doesn't stop, you may need `kill -9 <PID>`. Let me know if that helps!

Lite:

> Find the process on port 3000, then stop it:
>
> ```
> lsof -i :3000
> kill <PID>
> ```
>
> If it ignores that, use `kill -9 <PID>`.

Full:

> ```
> lsof -i :3000
> kill <PID>
> ```
>
> PID from second column. Stuck: `kill -9 <PID>`.

Ultra:

> ```
> lsof -i :3000
> kill <PID>
> ```
>
> Stuck → `kill -9`.

## Diagnosis: a failing import

Normal:

> It looks like the error you're seeing, `ModuleNotFoundError: No module named 'yaml'`, is happening because the PyYAML package isn't installed in the virtual environment that your script is running in. Looking at `tools/build.py` line 3, the script imports `yaml`, but your `requirements.txt` doesn't list it. To fix this, add `PyYAML==6.0.2` to `requirements.txt` and reinstall your dependencies. That should resolve the issue.

Full:

> Cause: PyYAML missing from `requirements.txt`; imported at `tools/build.py:3`.
> Evidence: "ModuleNotFoundError: No module named 'yaml'"
> Fix: add `PyYAML==6.0.2` to `requirements.txt`, reinstall.

Ultra:

> `tools/build.py:3` imports yaml; not in `requirements.txt`. Add `PyYAML==6.0.2`.
> Err: "ModuleNotFoundError: No module named 'yaml'"

## Procedure with a hazard: remove a large file from git history

Full:

> 1. Back up: `git clone --mirror <url> backup.git`
> 2. Rewrite: `git filter-repo --path big.bin --invert-paths`
> 3. Re-add remote: `git remote add origin <url>`
>
> Warning: the next step replaces the shared history for everyone, so tell the team to stop pushing and to re-clone afterwards.
>
> 4. `git push --force --all`
>
> Check: `git count-objects -vH`

The warning stays a full sentence at every level, including ultra.

## A menu, cut

Question: "How do I undo my last commit? It is only on my machine."

Not this (a menu):

> Options: `git reset --soft HEAD~1` keeps changes staged; `--mixed` keeps them unstaged; `--hard` discards them; or `git revert HEAD` makes a new commit; or `git commit --amend` if you only want to change it.

This (the path that fits "undo, local only"):

> ```
> git reset --soft HEAD~1
> ```
>
> Commit gone, changes stay staged.

A different situation gets a different single path, not a longer list.

## A question that needs a branch

Question: "Should I use `rebase` or `merge` to update my branch?"

Full:

> Branch only yours: `git rebase main`. Others have it: `git merge main`.

Two branches, one line each, because the answer depends on a fact not given.
