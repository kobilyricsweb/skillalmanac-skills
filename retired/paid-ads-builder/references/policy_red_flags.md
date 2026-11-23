## Contents

- How to use this
- Red-flag table by vertical
- Special ad categories
- What the validator checks and what it cannot
- Where the real rules live

## How to use this

Read the section for the user's vertical, then check every headline, description, image text and landing page. Policy is decided by the platform and changes; this table lists patterns that commonly cause disapproval or account problems, as of 2026-11, unconfirmed against the live policies. A flag means stop and review, not that the ad is illegal.

## Red-flag table by vertical

| Vertical | Avoid in copy and landing page | Do instead |
|---|---|---|
| Any | "guaranteed", "risk-free", "100 percent", "miracle", "free money", repeated punctuation, ALL-CAPS words, "click here" | State the actual term: "30-day refund", "quote before work" |
| Any | Superlatives ("best", "#1", "leading", "top-rated") with no source | Name the source and year on the landing page, or drop the word |
| Any | Implying you know something about the viewer ("Are you diabetic?", "Struggling with debt?") | Describe the service: "Diabetes meal plans from a dietitian" |
| Health and wellness | Cure or treat claims, specific weight-loss amounts or timelines, before and after pictures, claims about diagnosing | Describe what the service is, who runs it, and link evidence; keep outcomes general |
| Health | Selling prescription drugs, supplements with disease claims, unproven treatments | Needs platform certification or is not allowed; check before drafting |
| Finance and investing | Guaranteed returns, "double your money", "get rich", "passive income" promises, no mention of risk | Show rates with the terms: APR, fees, term, who qualifies |
| Lending and credit | "No credit check", "instant approval", "pre-approved" with no disclosed terms | Disclose APR range, term, fees on the landing page and say "subject to approval" |
| Crypto, trading, binary options | Often needs prior platform authorisation or is blocked by region | Confirm status before building anything |
| Housing and rental | Naming who should live there ("families", "singles", "young professionals", "no kids", religion, nationality) | Describe the home: bedrooms, rent, location, amenities |
| Employment | Age, gender, or similar preference ("young", "recent grad only", "he will") | Describe the role, duties, pay range and requirements |
| Weapons, tobacco, adult, gambling | Restricted or blocked on most platforms, region-dependent | Confirm eligibility first; may need licence proof |
| Comparison and competitor | Competitor brand names in copy or false comparison | Compare only on facts you can show |

## Special ad categories

Housing, credit and employment ads have a special-category setting on Meta and similar limits on other platforms. When the plan's vertical is one of them:

1. Set `special_category` true in the plan and declare the category in the ad manager when creating the campaign.
2. Do not target by age, gender, postcode or lookalike audiences. Use a location radius that meets the platform's minimum, plus interests that are not proxies for protected traits.
3. Expect some targeting and reporting options to be removed; plan for broader reach and a higher CPC.

The validator reports `special_category_targeting` for any of age_min, age_max, gender, zip_codes, postal_codes or lookalike in the audience, and `special_category_unflagged` when the vertical is special but the flag is false.

## What the validator checks and what it cannot

Checks: the phrase patterns above in all ad copy (housing and employment wording only when the plan's vertical matches), restricted targeting keys, the special-category flag. Cannot: images and video, landing page text, disclaimers, trademark use, account history, regional law. List these under "Not checked" in the report.

## Where the real rules live

Read the advertising policy section of each platform's own help centre for the format and vertical, and the special-category page on Meta if housing, credit or employment applies. For finance, health and employment ads in the user's country, local advertising and consumer law also applies and is outside this skill; suggest the user ask their compliance contact.
