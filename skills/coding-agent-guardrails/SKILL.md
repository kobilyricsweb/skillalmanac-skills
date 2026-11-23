---
name: coding-agent-guardrails
description: Gives a coding agent a short decision procedure and two read-only scripts (a repo guardrail audit and a diff scanner) that catch destructive git commands, edits to generated or vendored files, skipped or weakened tests, scope creep and committed secrets. Use when the user says stop the agent doing dangerous things, add guardrails, it deleted my work, it force-pushed, it edited a generated file, it commented out failing tests, or asks whether a repo or a diff is safe for an agent. Not for writing hooks, general code review, application security testing, or when the user only wants a quick opinion and no repo or diff exists.
license: Apache-2.0
compatibility: The scripts need Python 3.9 or newer (standard library only), read local files only and use no network; the audit needs Git on PATH and a Git repository root (it runs read-only git check-ignore). Enforcement examples mention Claude Code settings files, the checklist itself is tool-neutral.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.2.0-review2"
  revision_credit: "git check-ignore audit by Codex (0.2.0-review1 patch)"
  network: none
---

# Coding agent guardrails

A rule the agent merely reads is advisory. A guardrail is a rule plus something that checks. Pick the exit that fits, do only that, and stop.

## Step 0: pick the job (stop at the first match)

1. **User wants a quick answer, has a word limit, or no repo/diff/log is available** (for example "my agent lost work, what happened?" with nothing attached): answer plainly in the allowed length. Say what you cannot know, give the 2-4 safest next actions (stop the agent, do not run `git gc`/`clean`, check `git reflog` and `git stash list`) and ask for the one input you need (`git reflog`, `git status`). No audit, no report block, no tables, no invented cause.
2. **User asks you to review a diff or the agent's changes**: go to step 2.
3. **User asks whether a repo is safe, or wants guardrails set up**: go to step 3.
4. **You are about to run a risky command yourself**: step 1, then continue the task.

## Step 1: before a risky action

Ask first (name the exact command or file; a general "go ahead" does not count) for: `git reset --hard`, `git clean -f`, `git checkout -- .`, `git restore .`, `git stash drop`, `git branch -D`, any force push, a push to main, amending or rebasing pushed commits, `rm -rf`, overwriting a file you did not create.

Never, unless the user names that exact flag: `--no-verify`, `--no-gpg-sign`, disabling a hook or CI check.

Rewrite instead of asking when a safer form exists: stash or a new branch instead of reset/clean; `--force-with-lease` only after approval; edit the generator or source (not `dist/`, `vendor/`, lockfiles, minified or "do not edit" files) and re-run the generator, asking if none exists.

Before touching a failing test, read the failure and fix the code under test. Do not delete, skip, `xfail`, loosen an assertion, raise a timeout or refresh a snapshot just to get green; if the test is wrong, say so and ask.

Do not print secret values (name the variable only). Stop and tell the user if staging shows `.env`, `*.pem`, `id_rsa`, `AKIA`, `ghp_`, `sk-`. Do not rewrite history unasked.

Scope: state the task in one sentence and the files you expect to touch. One extra file with a reason is fine; a refactor, formatting sweep or dependency bump is a separate request, so report it and skip it.

More safe forms and patterns: [references/risky-actions.md](references/risky-actions.md).

## Step 2: scan a diff

```bash
git diff HEAD | python scripts/diff_guard.py [--task-dirs src,tests]
```

It prints JSON: `verdict` CLEAN or REVIEW and `findings` (rule, file, line). Rules: removed-test, assertion-removed, skip-added, timeout-raised, snapshot-changed, generated-edited, secret-added, hook-bypass, outside-task. Exit 1 means REVIEW. Secret values are never printed.

Triage: secret-added, hook-bypass and skip-added/removed-test are blockers; generated-edited means redo it at the source; the others need one line of justification each. Report only what the script found plus anything you read yourself; do not invent findings. If the diff is small and CLEAN, say "no guardrail issues found" in one or two lines.

## Step 3: audit a repo

```bash
python scripts/guardrail_audit.py path/to/repo
```

One JSON object: `checks` (id, status pass/info/warn/fail, detail) and `summary`. Exit 1 = at least one fail. It scans file contents for AWS key ids, private key blocks, `sk-`/GitHub/Slack tokens and `password=`-style values (never prints them), skips files Git reports as ignored (real git check-ignore: negations, nested rules and global excludes honoured; tracked files are always scanned; if Git cannot decide, the check gitignore-authority fails and the audit is incomplete, not clean), and only reads. Do not edit it to hide a finding. What each id means and the usual fix: [references/audit-checks.md](references/audit-checks.md). If it crashes or Python is missing, check by hand: `.gitignore` covers `.env` and keys, no secret-looking files tracked, an instruction file listing do-not-edit paths, a test command, lockfiles, generated directories marked.

Rank findings: secrets first, then missing `.env` ignore, then protected-path and test-command gaps. Propose fixes as a small diff; apply only if the user agrees. If a deny rule or hook blocks your action, report it and ask; never work around it.

## Step 4: choose enforcement per rule

| Rule type | Weakest to strongest |
|---|---|
| Style or judgement | instruction file line (advisory) |
| Path or tool never touched | permission deny rule |
| Must be blocked every time | a hook |
| Secrets, tests, protected branches | repo-side too: pre-commit secret scan, CI test job, branch protection |

## Report (only for steps 2-3, keep it under 15 lines, shorter if the user set a limit)

```
Verdict: SAFE | NOT SAFE | REVIEW   (one-line reason)
Blockers: <rule/check ids with file:line, or none>
Fix first: <the 1-3 changes, as diffs, not yet applied>
Enforcement: <rule -> advisory | deny rule | hook | repo-side>
Not checked: <history, branch protection, CI config, nested .gitignore>
```

## Limits

- Scripts see files and diffs now, not git history, remote protection or CI. A secret in another shape (JWT, URL with inline password) is missed; files over 200,000 bytes are skipped.
- A checklist the agent follows is not a security boundary; only deny rules, hooks and repo-side controls hold.
