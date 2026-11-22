## תקציר

- זהו תוכן עמוד ה-skill באתר: צ'קליסט לפני פעולה לסוכן קוד, ובדיקת מוכנות של ריפו.
- הצ'קליסט מכסה: פקודות git הרסניות, קבצים מיוצרים או vendored, דילוג על בדיקות או החלשתן, הרחבת תחום העבודה בשקט, ו-secrets ב-commit.
- סקריפט קריאה-בלבד `guardrail_audit.py` מדווח JSON על: .gitignore, קבצי סוד חשופים, קובץ הוראות, רשימת נתיבים מוגנים, פקודת בדיקות, lockfile ותיקיות מיוצרות.
- נבדק רק על fixtures סינתטיים (3 מתוך 3 עברו). לא בוצעה השוואה with/without ולא בדיקה בכלים אחרים. טיוטה, לא לפרסום לפני סקירה אנושית.

---

# Listing page content: coding-agent-guardrails

**One line:** A pre-action checklist for coding agents plus a read-only audit of a repo's guardrail setup.

## What it does

The skill gives the agent a table of risky actions (destructive git, `rm -rf`, generated or vendored files, failing tests, scope creep, secrets, dependencies) with what to check before each one and when to stop and ask. It then ends every code task with a finish line: run the declared tests, report honestly, list the files changed. A bundled Python script audits a repository directory and prints strict JSON about the setup that makes those rules enforceable. The skill also says which level enforces each rule (instruction line, deny rule, hook, repo-side control) so that advisory rules are not mistaken for protection.

## Capabilities

- A ten-row pre-action checklist with the exact "ask" conditions
- `scripts/guardrail_audit.py`: `.gitignore` coverage of `.env`, key files and credentials; secret-looking files present and not ignored; credential patterns inside file contents (AKIA keys, private key blocks, `sk-` and `ghp_` tokens, `password=`); instruction file present; protected-path list or deny rules; hooks configured; test command declared; lockfile next to each manifest; generated or vendored directories marked, ignored or declared
- Reference files: safe forms of destructive git commands, test-cheating patterns, secret name and value shapes, and the meaning and fix of every audit check id
- A fixed report with a "Not checked" line

## When to use / when not to

Use when the user wants an agent to stop doing dangerous or sloppy things, or wants to know whether a repo is safe to give to an agent. Not for writing the hooks themselves (a hooks skill does that and is named as one enforcement option), reviewing a diff, recovering from an incident, or testing an application's security.

## Requirements

Python 3.9 or newer for the audit (standard library). No network. The checklist is tool-neutral; the settings-file checks read `.claude/settings.json`.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run has been saved yet, so there are no agent transcripts here. Real output from the audit script on the bundled fixtures:

1. `python scripts/guardrail_audit.py evals/fixtures/bad` returns 3 fail and 8 warn: no `.gitignore`, `.env` present and not ignored, no instruction file, no deny rules or hooks, npm placeholder test script, no lockfile, unmarked `dist` and `vendor`. Exit code 1.
2. `python scripts/guardrail_audit.py evals/fixtures/good` returns 0 fail and 0 warn: 12 passes. Exit code 0.
3. `python scripts/guardrail_audit.py evals/fixtures/leaky` fails `secret-values-in-files`: `config.txt:3 aws-access-key-id`, `deploy_notes.txt:1 private-key-block`, `settings.json:1 password-assignment`. The ignored `.env` in the same fixture holds an `sk-` token and is not reported. Exit code 1.

## Limits

- The audit reads files present now; it does not read git history, branch protection, CI settings or nested `.gitignore` files.
- Pattern and name checks catch common cases only. Content scanning covers six documented credential shapes and skips `.gitignore`d files.
- Overlap: `agent-hooks-authoring` writes the hooks (this skill only names them as an enforcement level); `agent-instruction-files` audits the AGENTS.md or CLAUDE.md text, while this audit only checks that a protected-path list exists. The two audits do not contradict each other.
- A checklist the agent follows by choice is not a security boundary; only deny rules, hooks and repo-side controls hold when it does not cooperate.

## Evidence

See `VERIFICATION.md`. In short: lint 0 fail and 0 warn; script fixtures 4 of 4 match their expected output. Not tested: whether the skill changes agent behaviour (no with and without run), triggering in any tool, other tools, human review.

## Demo script (60 to 90 seconds)

To be written from a saved real run after the task evals exist. Planned beats: (1) prompt "is this repo safe for an agent?"; (2) the audit runs and shows the exposed `.env`; (3) the agent proposes a three-line `.gitignore` diff and waits; (4) the agent is then asked to make a failing test pass and fixes the code rather than the test.

## FAQ seeds

1. Does it need network access? No.
2. Does the script change my files? No, it only reads.
3. Is this a security tool? No. It reduces accidents; it is not a boundary.
4. How is it different from a hooks skill? It is the checklist and the audit; hooks are one way to enforce a rule.
5. Does it work in tools other than Claude Code? The checklist is tool-neutral; only the settings-file check reads Claude Code files. Not yet tested elsewhere.
6. Will it find a secret already committed? No; it does not read git history.
7. How do I uninstall it? Delete the skill folder.

## Changelog

0.1.0, 2026-11-21: first draft; lint and fixtures only.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Author: Skill Almanac Editorial. Accountable editor: Global Media Holdings. Drafted by an AI model (claude-sonnet-5-5); no independent human review yet.
