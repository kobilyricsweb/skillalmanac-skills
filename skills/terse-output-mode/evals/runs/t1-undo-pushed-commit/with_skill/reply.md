Use `git revert`. New commit cancels old one. History stays intact for teammates.

```
git revert HEAD
git push origin main
```

Warning: do not use `git reset` followed by `git push --force` on main, because teammates already pulled the commit and a force push rewrites history under them and can lose their work.
