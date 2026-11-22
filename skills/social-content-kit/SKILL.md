---
name: social-content-kit
description: Repurposes one source (article, release, talk) into platform-specific social posts and a dated content calendar, then validates the calendar with a script (strict JSON) for posts over character limits, sponsored posts without disclosure, duplicates within N days, bad posting gaps, hashtag overuse and engagement bait. Use when the user says repurpose this into LinkedIn and X posts, make a content calendar, schedule posts from this blog, or check my posting schedule. Do not use for paid ad copy, campaign strategy briefs, landing page copy, posting through APIs, or buying followers.
license: Apache-2.0
compatibility: The validation script needs Python 3.9 or newer, standard library only, no network. Without Python, follow the manual checks in step 6.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Social content kit

Turn one source into posts that differ by platform, and prove the calendar is clean before anyone schedules it. You write and check; you never publish, log in or call a platform API.

## Inputs to settle first

Ask only for what is missing: the source (file or pasted text), the platforms (default LinkedIn, X, Instagram when the user names none), the start date and time zone, the link to put in posts, and whether any post is paid or sponsored (who pays, what the sponsor requires). If a sponsor exists, every post about the sponsor's product is `sponsored: true`.

## Workflow

```
- [ ] 1 Extract atoms from the source
- [ ] 2 Map atoms to platforms and days
- [ ] 3 Write each post
- [ ] 4 Write the calendar file
- [ ] 5 Run the validator, fix, re-run
- [ ] 6 Report
```

1. **Extract atoms.** Read the source once and fill the atom table (id, type, exact content, source location) described in [references/writing_rules.md](references/writing_rules.md), section "Repurposing atoms". Copy figures and quotes exactly. Fewer than 4 atoms: tell the user the source is too thin for a calendar and stop.
2. **Map.** One primary atom per post; no atom twice on the same platform within 14 days; the same atom on two platforms only in two different forms. Use the cadence table in the same reference: launch on day 0, then days 2, 5, 9, 13.
3. **Write.** Apply the hook rules and the no-bait rules from the same reference. Check each platform's text cap, fold, link handling and hashtag norm in [references/platform_limits.md](references/platform_limits.md); read only the rows for the platforms in use. Never add a number, quote or claim that is not in the source.
4. **Write the calendar** to `calendar.json` or `calendar.csv`, starting from [assets/calendar_template.csv](assets/calendar_template.csv). Fields: `id`, `platform` (x, linkedin, instagram, facebook, threads, bluesky, tiktok, youtube), `scheduled_at` (ISO 8601 with UTC offset), `text` (exactly what will be published), `sponsored` (true or false), optional `disclosure` (`platform_label` when the paid-partnership label is switched on, Instagram, Facebook, TikTok, YouTube only), optional `hashtags`. JSON may be a list or `{"posts": [...]}`.
5. **Validate.**

```bash
python scripts/calendar_check.py calendar.json
```

   Run it, fix every `error`, decide each `warning` (fix it, or keep it and say why in the report), run again. Do not edit the script or the limits to make a check pass; if a platform's real limit has changed, pass `--limits changed.json` and say so in the report. Options: `--dup-days N` (default 14), `--min-gap-minutes N` (overrides every platform), `--max-gap-days N` (default 10), `--rules` (prints the limits table in use).
   Manual fallback without Python: count characters per post against the table, find every `sponsored` post and confirm a marker before the fold, compare posts pairwise inside 14 days, check the gap per platform against the cadence table, and count hashtags.
6. **Report** in this fixed shape, after the calendar:

```
Posts: <n by platform>, <date range>
Validator: ok <true|false>, <errors> errors, <warnings> warnings (limits as of <date>)
Warnings kept: <code, post id, reason>
Disclosure: <sponsored post ids and the marker used, or "none sponsored">
Needs a source: <anything not in the source that a post relies on>
Not checked: <images, link previews, platform rules changed after the table date, local advertising law>
```

## Validator output contract

Stdout is one JSON object, ASCII only:

```
{"tool": "calendar_check", "version": "1.0.0", "limits_as_of": "YYYY-MM-DD", "file": "<name>",
 "posts": <int>, "ok": <bool>, "errors": <int>, "warnings": <int>,
 "findings": [{"severity": "error|warning", "code": "<code>", "post_id": "<id or null>",
               "platform": "<name or null>", "message": "<text>", "detail": {...}}]}
```

Error codes: `missing_field`, `duplicate_id`, `unknown_platform`, `bad_sponsored_value`, `bad_datetime`, `over_limit`, `hashtag_count`, `missing_disclosure`, `duplicate_post`. Warning codes: `no_timezone`, `hashtag_count_high`, `hook_past_fold`, `engagement_bait`, `disclosure_not_upfront`, `undeclared_sponsored`, `gap_too_short`, `gap_too_long`, `unadapted_cross_post`. Exit 0 when `errors` is 0, 1 when any error, 2 for a missing, empty or malformed file or bad arguments (message on stderr, nothing on stdout).

## Boundaries

- Sponsored content: this skill never removes, hides or weakens a disclosure to make a post look organic. If asked to, decline that part.
- No fake engagement: no purchased followers, comments or reviews, no sockpuppet replies, no posts written as a customer who does not exist.
- Posts about real people or named customers use only what the source says about them.

## Limits

- The limits table is stated as of 2026-11-21 and rests on tool-vendor pages, not platform documentation; Instagram's hashtag cap is disputed. Every limit, fold, hashtag cap, image ratio and minimum gap that is not confirmed by a platform page is marked "verify (unconfirmed, as of 2026-11)" in references/platform_limits.md; treat those as editorial defaults and re-check before relying on one. Only X 280 and link weight 23, LinkedIn 3,000, Instagram caption 2,200, Threads 500 and Bluesky 300 are stated without that mark.
- Characters are counted as Unicode code points; X link weight of 23 is applied, X's extra weight for some scripts is not. Multi-code-point emoji are over-counted.
- Disclosure detection reads text only. It cannot see a video, an image overlay or whether the platform label is truly switched on; `disclosure: platform_label` is taken on trust.
- Duplicate detection is word overlap (80 percent) inside the window on the same platform; it does not judge whether two different posts say the same thing.
- Posting-time gaps check spacing only, not the best hour; no audience data is used.
- The skill does not check images, link previews, legality in a given country, or whether a post is true; the user owns those.
