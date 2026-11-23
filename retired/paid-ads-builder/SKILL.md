---
name: paid-ads-builder
description: Use when the user asks for a Google Ads, Microsoft Ads, Meta, LinkedIn or TikTok campaign plan, ad copy within character limits, a budget split, or a check of ads before launch. Builds one JSON plan with objective, audience, ad groups, keywords and negatives, copy, budget and bid arithmetic, a UTM and conversion definition and a launch checklist, then validates it with a script (copy over limits, missing negatives, no landing URL, UTM gaps, budget mismatch, banned claims). Do not use for brand strategy briefs, landing page copy, organic social posts, SEO, or managing a live account's bids.
license: Apache-2.0
compatibility: The validator needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual checks in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Paid ads builder

Produce one machine-checkable plan, not loose advice. The plan is a JSON file; the validator is the gate. Nothing is launched, bought or logged into by this skill: it plans and checks, the user presses the buttons.

## Inputs to collect first (ask once, in one message)

1. What is sold, at what price, and the gross margin (or profit per sale or per lead that closes).
2. Where people go after the click (one URL per ad group, https) and what counts as a win (the conversion).
3. Monthly budget, start date, location, platform(s) the user already has an account on.
4. Vertical: general, health, finance, housing, credit or employment. The last three are special categories (step 5).

If margin or the conversion is unknown, say so in the plan under `conversion.definition` as "assumed" and mark every CPA target as an assumption. Never invent a margin.

## Workflow

```
- [ ] 1 Pick platform by intent
- [ ] 2 Do the budget arithmetic (formulas below)
- [ ] 3 Write the plan JSON
- [ ] 4 Write copy inside the limits
- [ ] 5 Policy pass
- [ ] 6 Run the validator, fix, re-run
- [ ] 7 Hand over the launch checklist and the report
```

### 1. Pick the platform by intent

| Situation | Start with | Why |
|---|---|---|
| People already search for the product ("plumber near me") | Google or Microsoft search | Demand exists; you pay for the click that already wants it |
| Nobody searches for it yet, visual or impulse product | Meta or TikTok | You create demand; expect lower conversion rate, cheaper clicks |
| B2B, buyer defined by job title or company | LinkedIn | Only platform with reliable title targeting; clicks cost several times more |
| Budget under 600 per month in total | One platform, one campaign | Splitting starves both (step 2, test floor) |

Default for a small business with an existing search demand: one search campaign first, social retargeting only after 30 or more conversions exist.

### 2. Budget and bid arithmetic

Use exactly these formulas and write the results into the plan; the validator recomputes them.

```
daily_budget      = monthly_budget / 30.4        (campaign budget = daily_budget x days)
clicks            = budget / cpc
conversions       = clicks x cvr
cpa               = budget / conversions  = cpc / cvr
break_even_cpa    = profit per conversion  (price x gross margin; for leads: close rate x profit per sale)
target_cpa        = 0.7 x break_even_cpa   (house rule: keep 30 percent as margin for error)
break_even_roas   = 1 / gross_margin
```

Worked example: price 200, margin 40 percent gives profit 80, target CPA 56. With cpc 2.50 and cvr 4 percent, cpa = 2.50 / 0.04 = 62.50, which is above 56, so either the landing page must convert better, the cpc must fall, or the offer is not viable on this platform. Say that in the report instead of hiding it.

Rules that carry numbers (heuristics, not platform rules):

- Test floor: a campaign needs budget for at least 100 clicks per ad group, i.e. `budget >= 100 x cpc x ad_groups`. Below that, cut ad groups.
- Automated bidding (target CPA, max conversions, target ROAS) needs about 30 conversions per campaign per month. Fewer: start manual cpc or max clicks and switch later. The validator warns under 30.
- Kill rule: pause a keyword, ad set or ad after spend of 3 x target CPA with zero conversions. Review weekly, not daily; daily edits reset learning.
- Split of the first month: 70 percent proven intent (exact and phrase match, or the best audience), 20 percent expansion, 10 percent experiments.

Read [references/budget_and_bids.md](references/budget_and_bids.md) for platform learning thresholds, match-type behaviour and a worked three-campaign split.

### 3. The plan JSON (output contract)

Save as `ad_plan.json`. All fields below; extra fields are allowed and ignored.

```
{
  "business": str, "vertical": "general|health|finance|housing|credit|employment",
  "special_category": bool, "currency": "USD", "total_budget": number, "target_cpa": number,
  "conversion": {"name": str, "definition": str, "window_days": number},
  "limit_overrides": {"google_search": {"headline": 30}},          optional
  "campaigns": [{
    "name": str, "platform": "google_search|microsoft_search|meta|linkedin|tiktok",
    "objective": str, "bid_strategy": str, "audience": object,
    "daily_budget": number, "days": number, "budget": number,
    "utm_campaign": str,
    "forecast": {"cpc": number, "cvr": number, "clicks": number, "conversions": number},
    "negative_keywords": [str],
    "ad_groups": [{
      "name": str, "landing_url": "https://...?utm_source=..&utm_medium=..&utm_campaign=..",
      "keywords": [str], "negative_keywords": [str],
      "ads": [ search: {"headlines":[...],"descriptions":[...],"path1","path2"}
               social: {"primary_text","headline","description"} ]
    }]
  }]
}
```

Structure contract, one line each: one objective per campaign; one audience per ad set; one landing page per ad group; one theme per ad group (if two keywords need different ad text, they are two groups); match types written with syntax (`[exact]`, `"phrase"`, plain broad); negatives at campaign level for words that are never wanted, at ad group level to keep sibling groups apart. Seed negatives: free, jobs, salary, diy, course, reviews, template, and the user's own competitors only if the user says to exclude them.

### 4. Copy rules

- Count characters with the script, not by eye. Limits per platform and field are in [references/platform_limits.md](references/platform_limits.md); every limit there is marked "verify (unconfirmed, as of 2026-11)" because platforms change them. If the user's ad manager shows a different limit, put it in `limit_overrides` and say so.
- Search: 3 to 15 headlines and 2 to 4 descriptions per ad (verify). Each headline must stand alone, because they are shown in any order. Put the keyword theme in 1 headline, a concrete offer or price point in 1, a proof point in 1, a call to action in 1.
- Social: the first 125 characters of primary text carry the message; the rest is cut behind "see more" (verify). One idea per ad.
- Every claim in copy must be visible on the landing page. No superlative without a source. No exclamation mark in search headlines.

### 5. Policy pass

Run the table in [references/policy_red_flags.md](references/policy_red_flags.md) over every headline, description and landing page. Fast version: health (no cures, no before/after, no "do you have X"), finance (no guaranteed returns or approval, disclose fees and rates), housing, credit and employment (set `special_category` true; no age, gender or postcode targeting; no copy about who the occupant or hire should be). The validator catches the wording; it cannot judge the landing page. The final decision belongs to the platform and the user.

### 6. Validate

```
python scripts/validate_ad_plan.py ad_plan.json
```

Prints strict JSON: `valid`, `summary.errors`, `summary.warnings`, and `findings[]` with `severity`, `code`, `path`, `message`. Exit 0 when there are no errors, 1 on errors, 2 when the file cannot be read. Add `--strict` to fail on warnings. Fix the plan and re-run until `valid` is true; read warnings and either fix them or list them in the report as accepted risks. Do not edit the script to pass; do not delete the offending copy without replacing it.

Codes: copy_over_limit, copy_exclamation, rsa_headline_count, rsa_description_count, negatives_missing, negatives_thin, negative_blocks_keyword, keyword_overlap, landing_url_missing, landing_url_invalid, utm_missing, utm_format, utm_inconsistent, utm_campaign_mismatch, utm_source_varies, budget_mismatch, total_budget_mismatch, forecast_clicks_mismatch, forecast_conversions_mismatch, cpa_above_target, bid_learning_data_thin, conversion_undefined, special_category_targeting, special_category_unflagged, claim_* (absolute, health, finance, housing, employment, personal_attribute, superlative, style).

Manual fallback with no Python: add up campaign budgets against `total_budget`, multiply daily by days, recompute clicks, conversions and CPA, count characters of every headline in a spreadsheet, list every ad group's URL with its three UTM values side by side, and grep the copy for the words in [references/policy_red_flags.md](references/policy_red_flags.md).

### 7. Hand over

Give the user the plan JSON, the validator output, and the report below. Measurement setup (UTM naming, conversion definition, what to review weekly) is in [references/measurement_plan.md](references/measurement_plan.md); the pre-launch list is in [references/launch_checklist.md](references/launch_checklist.md). Read the checklist before the handover and paste only the items still open.

## Report format

```
Plan: <file>   Platforms: ...   Monthly budget: ...   Target CPA: ... (assumed|derived from margin)
Validator: valid <true|false>, <n> errors, <n> warnings (list accepted warnings and why)
Forecast: <conversions> conversions at CPA <x> (formula and inputs shown); gap to target: <y>
Policy flags: <list, or "none found by wording check; landing page not reviewed">
Open before launch: <checklist items still undone>
Not checked: CPC and conversion-rate inputs are estimates; character limits unverified against the live ad manager; landing page content; account policy status
```

## Limits

- CPC, conversion rate and every forecast are inputs supplied by the user or assumed; the skill does arithmetic on them and cannot predict real auction prices.
- Character limits and asset counts are unconfirmed as of 2026-11 and are the first thing to check in the live ad manager.
- The claim check is wording-based. It misses images, video and landing pages, and it will flag some acceptable phrases; a flag is a prompt to review, not a ruling.
- It does not log in, create accounts, spend money or submit ads. It does not give legal advice; regulated verticals need the user's own compliance review.
- Not for keyword research (use keyword-demand-research), campaign positioning briefs (marketing-campaign-brief) or landing page copy (copywriting-landing-pages).
