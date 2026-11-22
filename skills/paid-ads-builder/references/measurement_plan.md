## Contents

- Conversion definition
- UTM contract
- Naming rules
- Checks before launch
- Reading the first two weeks

## Conversion definition

Write the conversion as a sentence with four parts, and store it in `conversion.definition`:

```
Event:   what happens (thank-you page /quote/thanks loaded)
Counted: once per session | every time
Window:  days after click that still count (30)
Excluded: what does not count (test submissions, internal IPs, phone calls under 60 seconds)
```

Rules: pick one primary conversion per campaign. Secondary actions (newsletter, page view of pricing) may be tracked but must not be the optimisation target unless the primary has too few events (see learning thresholds in `references/budget_and_bids.md`). The conversion must fire on the success state, not on the button click. Test it with a real submission before launch.

## UTM contract

Every landing URL carries exactly these parameters, all lowercase, no spaces:

| Parameter | Rule | Example |
|---|---|---|
| utm_source | Platform, one value per platform for the whole account | google, bing, meta, linkedin, tiktok |
| utm_medium | Traffic type, a small fixed set | cpc for search, paid-social for social |
| utm_campaign | Campaign slug plus month, identical in every ad group of the campaign | search-plumbing-2026-12 |
| utm_content | Optional; ad group or creative id, used to compare creatives | emergency |
| utm_term | Optional; usually filled by the platform's keyword ValueTrack or equivalent | leave to the platform |

Why: analytics tools treat `Google` and `google` as different sources, and a missing medium sends traffic to "(not set)" or direct. The validator reports `utm_missing` and `utm_format` per URL, `utm_inconsistent` when ad groups of one campaign disagree, `utm_campaign_mismatch` when the URL disagrees with the campaign's declared `utm_campaign`, and `utm_source_varies` when one platform uses several source values across campaigns.

Where the platform can append tracking at account level (a tracking template), use it instead of hand-typing URLs, and put the same values into the plan for checking. Do not put personal data (names, emails, phone numbers) in any URL parameter.

## Naming rules

- Campaign: `<platform>-<theme>-<yyyy-mm>`; ad group: `<theme>`; ad: `<angle>-<version>`.
- Never reuse a utm_campaign for a different offer; reports will blend them.
- Keep a one-page sheet mapping utm values to campaign names and store it with the plan.

## Checks before launch

1. Click each ad's final URL from the ad manager preview; the address bar shows all three required UTM parameters.
2. Submit a test conversion; it appears in analytics under the expected source and medium within the platform's normal delay.
3. The conversion count in the ad platform and in analytics are within about 20 percent after a week; larger gaps usually mean double counting, a window mismatch or consent-banner loss.
4. Consent or cookie banner behaviour is tested, because declined consent hides conversions in some setups.

## Reading the first two weeks

Do not judge CPA before 3 x target CPA has been spent on the campaign or 14 days have passed. Compare real CPC and cvr with the forecast; when either is more than 30 percent off, rewrite the forecast in the plan and re-run the validator so the arithmetic stays honest.
