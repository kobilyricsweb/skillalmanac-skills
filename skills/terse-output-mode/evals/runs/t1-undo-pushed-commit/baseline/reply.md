Commit pushed to main, teammates pulled. Do NOT rewrite history. Use revert.

    git checkout main
    git pull
    git revert HEAD
    git push origin main

Revert make new commit that cancel old one. History stay. Teammates just pull. No pain.

Revert merge commit? Need mainline flag:

    git revert -m 1 HEAD

Want undo but keep changes in files? Revert without commit:

    git revert -n HEAD

Fix, then commit and push.

Do not do `git reset --hard` + `git push --force` on main. Teammates already have old commit. Force push make their history diverge. Big mess, lost work, angry team.

Only force push if secret leaked (password, key). Then rotate secret first, tell team, and coordinate. Force push alone not enough, secret already out.
