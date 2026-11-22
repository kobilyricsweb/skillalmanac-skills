---
name: coding-agent-guardrails
description: Gives a coding agent a pre-action checklist that prevents destructive git commands, edits to generated or vendored files, skipped or weakened tests, silent scope creep and committed secrets, and audits a repo's guardrail setup with a read-only script. Use when the user says stop the agent doing dangerous things, add guardrails, make the agent safer, it deleted my work, it force-pushed, it edited a generated file, it commented out failing tests, or asks whether a repo is safe to let an agent loose in. Do not use for writing hooks themselves, code review of a diff, or application security testing.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer (standard library only) and reads the repo directory it is given. No network access is used. Enforcement examples mention Claude Code settings files, the checklist itself is tool-neutral.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Coding agent guardrails

Instructions are guidance; a guardrail is guidance plus something that checks. This skill does two jobs: it makes the agent run a short checklist before each risky action, and it audits whether the repo has the files and settings that make those rules enforceable.

## When this applies

Apply the checklist in step 1 to every session in a repo where the user asked for guardrails, and to any single action that matches a row of the table. Run the audit (step 3) when the user asks whether a repo is safe or wants guardrails set up.

## Workflow

### 1. Pre-action checklist

Before the action, find its row. If the row says "ask", stop and ask in plain words naming the exact command or file; do not proceed on a general "go ahead".

| Action | Before doing it | Rule |
|---|---|---|
| `git reset --hard`, `git clean -f`, `git checkout -- .`, `git restore .`, `git stash drop`, `git branch -D` | Run `git status` and `git diff --stat`; name what would be lost | Ask unless the user named this operation. Prefer a reversible form (stash, new branch) |
| `git push --force`, push to main, amend or rebase pushed commits | Check the branch and its remote | Ask every time. Never push or commit unless the user asked |
| `--no-verify`, `--no-gpg-sign`, disabling a hook or CI check | None | Never, unless the user explicitly asks for that exact flag |
| `rm -rf`, overwriting a file you did not create, `mv` onto an existing file | Resolve the absolute path; list what is inside | Stay inside the repo. Ask when anything untracked is in the way |
| Editing a file under a generated, vendored or build directory, a lockfile, a minified file, or a file whose first lines say it is generated | Look for the marker, then find the source or the generator | Edit the source and re-run the generator. If none exists, ask |
| Making a failing test pass | Read the failure first | Fix the code under test. Never delete, skip, `xfail`, loosen an assertion, raise a timeout or refresh a snapshot just to get green. If the test is wrong, say so and ask |
| Starting a task | Write the task in one sentence and list the files you expect to touch | One extra file is fine if you say why. A different area, a refactor, a formatting sweep or a dependency bump is a separate request: report it, do not do it |
| Reading, printing or copying `.env`, keys, tokens, credentials files | None | Do not print values. Name the variable, never its value. Do not paste secrets into commands, logs or commit messages |
| Staging or committing | `git diff --cached --name-only`, then read the list | Stop if a secret-looking file or value appears (`.env`, `*.pem`, `id_rsa`, `AKIA`, `ghp_`, `sk-`, long random strings). Tell the user; do not rewrite history unasked |
| Adding or upgrading a dependency | State the package and why | Only when the task needs it. Never hand-edit a lockfile |

Details, safer alternatives and detection patterns: read [references/risky-actions.md](references/risky-actions.md) when the action is in the git, test or secret rows and you are unsure of the safe form.

### 2. Finish line for any code task

Before saying done: run the repo's declared test command (the audit shows it); report the result in your own words with the failing test names if any; list the files changed and confirm each belongs to the task. If there is no test command, say that, and say nothing is verified.

### 3. Audit the repo's guardrail setup

```bash
python scripts/guardrail_audit.py path/to/repo
```

It scans file CONTENTS as well as names: AWS access key ids (`AKIA` plus 16 characters), `-----BEGIN ... PRIVATE KEY-----` blocks, `sk-` tokens of 20 or more characters, `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` GitHub tokens, `xox*-` Slack tokens and `password=`, `passwd`, `pwd`, `secret` or `api_key` assignments with a value of 8 or more characters (placeholders such as `changeme`, `<...>`, `${...}` are skipped). Files matched by the root `.gitignore` are not scanned, and the report gives file, line and kind, never the value.

Run the script; do not edit it to make a finding go away. It prints one JSON object: `checks` (each with `id`, `status` pass, info, warn or fail, and `detail`) and a `summary`. It only reads; it never changes the repo. Exit code 1 means at least one fail. Read [references/audit-checks.md](references/audit-checks.md) for what each check id means and the usual fix. Without Python, walk the same list by hand: `.gitignore` entries for `.env` and key files, secret-looking files present, an instruction file with a do-not-edit list, a test command, lockfiles, and generated or vendored directories marked.

Propose fixes as a small diff and apply them only when the user agrees.

### 4. Choose how each rule is enforced

| Rule type | Enforcement, weakest to strongest |
|---|---|
| Style or judgement ("keep changes small") | instruction file line |
| A path or tool never to be touched | permission deny rule in the agent settings |
| Must happen or be blocked every time, with logic | a hook; if the skill `agent-hooks-authoring` is installed, use it to write and test the hook |
| Secrets, tests, protected branches | also repo-side: pre-commit secret scan, CI test job, branch protection, because those hold even when the agent does not |

Say which level each rule is at. A rule that exists only as an instruction line is reported as "advisory".

### 5. Report

```
Guardrail audit: <repo>
Failed: <check ids with one-line reasons, or none>
Warned: <check ids>
Enforcement: <rule -> advisory | deny rule | hook | repo-side>
Changes proposed: <diffs, not yet applied>  /  applied: <list>
Not checked: <e.g. branch protection, CI config, nested .gitignore files, history>
```

## Limits

- The audit looks at files present now. It does not read git history, remote branch protection, CI settings or nested `.gitignore` files, and cannot tell whether a secret is already committed.
- Content patterns are the six listed in step 3; a secret in another shape (a bare base64 string, a JWT, a database URL with an inline password) is not found. Files over 200,000 bytes and binary files are not read.
- Name and pattern checks catch the common cases; a determined bypass or an unusual layout will get past them.
- A checklist the agent chooses to follow is not a security boundary. Only deny rules, hooks and repo-side controls hold when the agent does not cooperate.
- Generated-directory detection uses well-known folder names (`dist`, `vendor`, `generated` and similar); other names are not found.
