# Listing page content: social-content-kit

**One line:** Turns one article, release or talk into platform-specific posts and a calendar that a script has checked.

## What it does

The agent extracts 6 to 10 "atoms" (figures, quotes, decisions, mistakes) from the source, assigns each to one post per platform, writes posts under fixed hook and no-bait rules, and saves a calendar as JSON or CSV. A validator script then checks the calendar against a per-platform limits table stated as of 2026-11-21 and prints strict JSON. A fixed report lists warnings kept, the disclosure marker used for each sponsored post and what was not checked.

## Capabilities

- `scripts/calendar_check.py`: errors for over-limit text (X links counted as 23), missing or unclear disclosure on `sponsored: true` posts, duplicate posts within N days, hashtag counts over the hard limit, bad dates, unknown platforms; warnings for hashtag overuse, hook past the fold, engagement bait, disclosure after the fold, gaps too short or too long, identical text across platforms, missing time zone
- Limits table with confidence per row, link handling, hashtag norms, image ratios
- Hook rules, no-bait rules, disclosure rules, atom table, cadence defaults
- A calendar template (`assets/calendar_template.csv`)

## When to use

You have one source and want LinkedIn, X, Instagram, Threads, Bluesky, Facebook, TikTok or YouTube text plus a schedule, or you have a calendar export and want it checked before scheduling.

## When not to use

Paid ad copy, campaign strategy, landing pages, posting through platform APIs, buying followers or engagement. How it differs from neighbouring skills: `marketing-campaign-brief` produces the strategy (audience, positioning, budget); this skill starts from a finished source and produces posts and a checked schedule. `copywriting-landing-pages` writes page copy; this skill writes feed posts and never page sections.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual checks in SKILL.md step 5.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs below are from a real run of the script on the saved fixtures (`python evals/run_fixtures.py`, 5 of 5 pass). No with-skill agent run exists yet, so no agent-written posts are shown.

1. `python scripts/calendar_check.py evals/fixtures/good_calendar.json` returns `"posts": 6, "ok": true, "errors": 0, "warnings": 0`, exit 0.
2. `python scripts/calendar_check.py evals/fixtures/bad_calendar.csv` returns `"posts": 11, "ok": false, "errors": 6, "warnings": 7`, exit 1. Two of the findings:

```
{"severity": "error", "code": "missing_disclosure", "post_id": "b3", "platform": "instagram",
 "message": "sponsored post has no clear disclosure: only an unclear tag (#sp)"}
{"severity": "warning", "code": "disclosure_not_upfront", "post_id": "b8", "platform": "instagram",
 "message": "disclosure starts at character 228, after the 125-character visible window"}
```

## Limits

- Limits table rests on tool-vendor pages checked 2026-11-21, not platform documentation; Instagram's hashtag cap is disputed.
- Characters counted as code points; multi-code-point emoji are over-counted; X's extra weight for some scripts is not applied.
- Disclosure detection is text only; the platform label is taken on trust.
- Duplicate detection is word overlap on the same platform; gaps check spacing only, not the best hour.
- Images, link previews, local advertising law and truthfulness are not checked.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN and 5 script fixture cases pass. Not tested: any with/without agent comparison, trigger behaviour, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste an article; the agent shows the atom table.
2. It writes posts for three platforms and saves `calendar.json`.
3. `calendar_check.py` reports an error: a sponsored post has no disclosure and an X post is 340 characters.
4. The agent fixes both, re-runs, `ok: true`, and prints the report.

## FAQ seeds

- Does it post for me? No. It writes text and a calendar file; it never logs in or calls a platform API.
- Does it need network access? No.
- Are the character limits current? They are stated as of 2026-11-21 with a confidence per row; override any number with `--limits`.
- Will it hide that a post is sponsored? No; it declines that and the script errors on missing disclosure.
- How is it different from a campaign brief skill? That one decides the strategy; this one turns a finished source into posts and checks the schedule.
- Does it check images? No; the ratio table is guidance only.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
