# Listing page content: paid-ads-builder

**One line:** Builds a search or social ad campaign plan as checkable JSON, then validates copy, negatives, UTMs and budget arithmetic.

## What it does

The skill walks an agent through picking a platform by intent, doing the budget arithmetic with fixed formulas (clicks, conversions, CPA, break-even and target CPA), writing a plan in a defined JSON shape, and writing ad copy inside platform character limits. A standard-library script then validates the plan and prints strict JSON findings. References carry the limits table, a policy red-flag table by vertical, learning-phase thresholds, a UTM and conversion contract and a launch checklist.

## Capabilities

- `scripts/validate_ad_plan.py`: JSON report with `valid`, error and warning counts, and findings with code, path and message; exit 0, 1 or 2
- Checks: copy over limit, search headline asset counts, exclamation in search headlines, missing or thin negatives, a negative that blocks a keyword, keyword overlap between ad groups, missing or non-https landing URL, UTM missing, uppercase or inconsistent, daily x days against budget, campaign sum against total, forecast clicks and conversions recomputed, implied CPA against target, thin data for automated bidding, undefined conversion, banned claims by vertical, restricted targeting for housing, credit and employment
- A fixed hand-over report that ends with what was not checked

## When to use

You ask for a Google Ads, Microsoft Ads, Meta, LinkedIn or TikTok campaign plan, ad copy that fits the limits, a budget split, or a check of an existing plan before launch.

## When not to use

Not for campaign positioning briefs (see marketing-campaign-brief), keyword research (keyword-demand-research), landing page copy (copywriting-landing-pages), organic social posts (social-content-kit), SEO, or changing bids in a live account. How it differs from marketing-campaign-brief: that skill decides objective, audience and channel mix at brief level; this one produces the ad-level plan with copy, keywords, UTMs and the validator.

## Requirements

Python 3.9 or newer, standard library only. No network. No account access.

## Install

Copy the folder to `.claude/skills/paid-ads-builder/` or `.agents/skills/paid-ads-builder/`.

## Examples

Prompt: "Check this apartment ad plan before launch." Real output of `python scripts/validate_ad_plan.py evals/fixtures/housing_plan.json` (shortened to the finding codes):

```
valid: false   errors: 3   warnings: 0
error special_category_targeting campaigns[0].audience.age_min
error special_category_targeting campaigns[0].audience.gender
error claim_housing campaigns[0].ad_groups[0].ads[0].primary_text
```

Second example, `evals/fixtures/bad_plan.json` (a finance plan): 16 errors and 3 warnings, among them a 34-character headline against a limit of 30, "Guaranteed Approval", a missing landing URL, `utm_source` written both `Google` and `google`, budget 40 x 30 = 1200 against a stated 1500, and a total budget of 3000 against campaign budgets of 1500. `evals/fixtures/good_plan.json` returns `valid: true` with 0 errors and 0 warnings.

## Limits

CPC and conversion rate are user inputs or assumptions; character limits are unconfirmed as of 2026-11 and must be checked in the live ad manager; the claim check is wording-only and not a compliance ruling; no login, spend or submission is ever performed.

## Evidence

Static lint and script fixtures only; see VERIFICATION.md. No with/without efficacy eval, trigger test, cross-tool run or human review has taken place.

## Demo script (60 to 90 seconds)

1. Prompt: "Plan a Google search campaign for a roofing company, 2,400 budget" with the brief attached.
2. The agent asks nothing extra, computes profit per lead and target CPA, and writes `ad_plan.json`.
3. The validator flags one headline over the 30-character limit and a missing landing URL; the agent fixes both and re-runs to `valid: true`.
4. The agent prints the report: implied CPA 85.71 against target 398, plus the "Not checked" line.

(Storyboard only; a real recorded run does not exist yet.)

## FAQ seeds

- Does it need network? No.
- Does it log into my ad account? No; it plans and checks only.
- Are the character limits current? They are marked unconfirmed as of 2026-11; override them in the plan.
- Does it guarantee my ads get approved? No; the wording check is a prompt to review.
- How does it differ from marketing-campaign-brief? That one is the brief; this one is the ad-level plan and validator.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review yet.
