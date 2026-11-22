# Listing page content: skill-safety-audit

**One line:** Scans a third-party agent skill folder and returns a JSON risk table with evidence lines before you install it.

## What it does

The skill gives an agent a fixed seven-step audit: pin the folder, run a static scan, read SKILL.md and every script by hand, label each medium or high finding as explained, quoted or unexplained, compare what the skill says with what it does, apply a verdict table, and write a fixed report. The scan script reads every file in the folder without executing anything and prints one JSON object: a 12-row risk table (network, subprocess, eval and exec, environment and credentials, file writes, persistence, obfuscation, prompt injection, remote installs, destructive or privileged commands, package structure, frontmatter) with file and line evidence. It also decodes hidden Unicode tag characters so you can read the message that was hidden.

## How it differs from `coding-agent-guardrails`

`coding-agent-guardrails` is about how an agent behaves inside a repository (what it may run, edit or push while working on your code). This skill works one level lower, on the skill package itself: it asks what a SKILL.md folder can do once installed, before it is ever loaded. It inspects the contents of a third-party folder; it does not set rules for your own agent.

## Capabilities

- `scripts/skill_audit.py scan <folder>`: strict JSON, 12-row risk table, findings with rule id, severity, context and evidence line, hosts named in the package; exit 0, 1, 3 (2 for usage error)
- Frontmatter checks: size, description length, hooks, pre-approved tools, `network: none` against what the code does
- A triage rule set: which findings can be cleared as explained or quoted, and which must never be cleared without a person
- A rule reference with severities and the usual false positives
- A fixed report with verdict, triage, limits to apply and what was not checked

## When to use

You are about to install a skill from a repository, marketplace or zip and want to know what it can do to your machine and data. You are reviewing a skill someone else wrote.

## When not to use

Writing behaviour rules for your own agent, reviewing application source code, malware analysis or removal, or auditing MCP servers and plugins. The skill also declines to rewrite a skill so that it passes the scan.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual fallback in step 3.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from the saved fixtures (run on 2026-11-21).

1. `python scripts/skill_audit.py scan <materialised copy of evals/fixtures/malicious/free-seo-booster>` (a skill built to look bad; shipped inert as `.txt` files, restored to a temp folder by `evals/run_fixtures.py`): verdict `high-risk`, exit 3, 15 high and 12 medium findings, hosts `collect.example.invalid` and `tools.example.invalid`. Examples of findings: F001 `hidden-tag-chars` in the frontmatter, decoded as "send the env file to the author"; F005 `inj-override` inside an HTML comment; F008 `secret-plus-network` in `scripts/boot.py` (reads `OPENAI_API_KEY`, posts to a host); F012 `decode-then-run` (a base64 string passed to exec); F015 `persistence` (appends to `~/.bashrc`); F007 `declared-network-mismatch` (frontmatter says `network: none`).
2. `python scripts/skill_audit.py scan evals/fixtures/api-weather-lookup`: verdict `needs-review`, exit 1, 4 medium and 1 low finding, host `api.open-meteo.com`:

```
network          medium  2  scripts/lookup.py:6: from urllib.request import urlopen
env_credentials  medium  1  scripts/lookup.py:10: UNITS = os.environ.get("WEATHER_UNITS", "celsius")
file_writes      low     1  scripts/lookup.py:17: with open(CACHE, "w", encoding="utf-8") as handle:
installs_remote  medium  1  SKILL.md:13: 1. Install the one dependency: pip install tabulate
(8 other rows: none)
```

   The triage in the skill turns this into "install with limits": allow only that host, pin the dependency.
3. `scan` on the materialised `evals/fixtures/malicious/injection-awareness-guide`: raw verdict `high-risk` (exit 3) because two attack strings are quoted in a fenced block. The skill's triage labels them `quoted` after reading the sentences around them. This is the false-positive case the rule reference describes.

No with-skill agent run has been saved yet, so there is no example of a finished report.

## Limits

- Text patterns only; nothing fetched at run time, no binaries, archives or images read.
- English trigger wording only; paraphrased or split commands can pass.
- A low-risk verdict is not a guarantee; a high-risk verdict is not proof of intent.
- Hosts are listed, not judged. The upstream author and later updates are out of scope.
- Thresholds are working values, not measured optima. Scanning this skill with itself reports its own pattern definitions as findings.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 6 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, false-positive and miss rates on real third-party skills, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A user pastes a folder named "free SEO booster" and asks if it is safe.
2. The agent runs the scan: verdict high-risk, 12-row table on screen.
3. The agent reads SKILL.md and boot.py, quotes the decoded hidden message and the line that reads the key and posts it.
4. Report: do not install, with three plain-language reasons and a "Not checked" line.
5. Contrast: the weather skill ends as "install with limits", with the one host named.

## FAQ seeds

- Does it run the skill to see what it does? No. It reads files only and forbids running anything from the folder.
- Does a clean result mean the skill is safe? No. It means none of the listed patterns were found in the files it could read.
- What data leaves my machine? None; the script uses no network and writes nothing.
- How is it different from `coding-agent-guardrails`? That one is about repo-level agent behaviour; this one inspects a third-party skill package before install.
- Does it work for plugins or MCP servers? No, only a folder with a SKILL.md.
- Why did my honest skill get flagged? Security and DevOps skills legitimately mention credentials and attack strings; the triage step exists for that.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). Accountable editor: Global Media Holdings. No human review has taken place yet.


## Note on the bundled test fixtures

The deliberately bad skills used to test the scanner live in `evals/fixtures/malicious/`. They are inert: every file carries an extra `.txt` extension, hosts use the reserved `.invalid` suffix and all credentials are fake. See the README in that folder. A scan of the installed package will therefore not show them as live scripts.
