# Habit tracker: is the topic growing?

**Short answer for your cofounder: no. Both of his numbers are real, but each is the wrong comparison. The topic is falling, and the "AI angle" is small and also falling.**

Question: habit tracker, US, English; go/no-go on pouring content into it.
Source: the user's keyword export `k2_habit_tracker_keywords.csv`, US, monthly, 2025-08 to 2026-10 (15 months, 9 keywords). The provider and fetch date are not stated in the file. The values look like ad-platform buckets, because close variants share identical numbers. Clustering run with `keyword_cluster.py`; output in `clusters.csv`.

## Working figure
- **26,500 searches/month** (de-duplicated, 12-month average for 2025-11 to 2026-10), in 7 clusters.
- Last month (2026-10): **15,430**.
- Raw sum for reference: 45,900 (9 keywords). 19,400 of that (42%) is double counting, because "habit tracker app/apps" and "best habit tracker app/apps" are the same search need with identical series.
- The 12-month average is inflated by the January 2026 spike (68,680). Excluding January the monthly average is about 23,100, and the last month is 15,430.
- Nothing was excluded as brand or off-topic. I did not supply brand or exclude patterns because the export contains none.

## Trend, with named windows

| Reading | Window | Result |
|---|---|---|
| Recent direction | Aug-Oct 2026 (avg 14,400) vs May-Jul 2026 (avg 18,840) | **falling, -23.6%** |
| Year on year | Aug-Oct 2026 vs Aug-Oct 2025 (avg 16,140) | -10.8% (head terms -7% to -23%) |
| Distance from peak | Oct 2026 vs Jan 2026 peak | **78% below peak** (15,430 vs 68,680) |
| Level | 12-month avg / last month | 26,500 / 15,430 |

Flags from the script: `one-off-spike`, `one-month-rebound-after-decline`, `78%-below-peak`.

## Checking the cofounder's two claims

**1. "Rebounded 20%+ last month."** The number is true. September to October 2026 went from 12,460 to 15,430 on the counted total (+24%). Most head terms went 6,600 to 8,100 (+23%). But:
- It is **one month, not a trend**. It follows Jun-Sep declines (Aug 15,300, Sep 12,460).
- October is back only to the July level (15,430), which is still well below the spring.
- Several of these steps are single volume-bucket moves (for example 6,600 to 8,100), so do not read them as precise.
- A later month would confirm it: **November and December 2026 must both come in above 15,430**. Do not plan on one month.
- Caution: the same data shows a big seasonal wave last winter (see below). Autumn rises into a New Year peak are likely seasonal, not growth.

**2. "The AI angle is up thousands of percent year over year."** Arithmetic, not growth. "ai habit tracker" was 0 in Aug-Sep 2025 and 10 in Oct 2025; the script's yoy of +35,900% compares 1,200 (Aug-Oct 2026 avg) to about 3 (Aug-Oct 2025 avg). This is a **new keyword in the last 12 months**, so quote absolutes: 10 searches in Oct 2025, 1,300 in Oct 2026. It is also:
- falling: Aug-Oct 2026 avg 1,200 vs May-Jul 1,600 (-25%);
- 32% below its own peak (1,900 in Apr-May 2026);
- only about 4% of the topic (avg 1,181 of 26,506).
It is a real, small niche that appeared recently. It is not a rescue for a falling head term. Note also that new terms show up in keyword tools with a delay, and demand inside AI assistants is not measured here at all.

## Season
The whole topic spikes in January (head terms 4x their October level) and decays through the year. This is the New Year's resolution pattern. The data has only one cycle (15 months), so write "possible season, one cycle seen". It strongly suggests the current "recovery" and the winter peak are seasonal, and that the spring and summer decline is the normal fall-off. A year-on-year comparison with a same-season year earlier is the right test, and Aug-Oct YoY is negative.

## Top clusters (12-month avg = Nov 2025 to Oct 2026)

| Cluster | Intent (rule-based) | Avg/mo | Trend, Aug-Oct vs May-Jul | YoY Aug-Oct | Variants |
|---|---|---|---|---|---|
| habit tracker app | transactional | 15,025 | falling -24% | -23% | 2 (plural) |
| best habit tracker app | transactional | 4,342 | falling -25% | -7% | 2 (plural) |
| free habit tracker app | transactional | 2,975 | falling -24% | -21% | none |
| how to build a habit tracker in notion | informational | 1,344 | falling -22% | -32% | none |
| ai habit tracker | unclassified (tool-seeking) | 1,181 | falling -25% | new keyword | none |
| habit tracker for adhd | unclassified | 823 | falling -18% | +85% (small base, 590 vs 320-390) | none |
| habit tracker widget iphone | unclassified | 817 | flat -13% | -6% | none |

The script returned three clusters as unclassified. I read them by eye: "ai habit tracker", "habit tracker for adhd" and "habit tracker widget iphone" are product or feature searches, which I would call tool-seeking.

## Composition
Almost all demand (22,300 of 26,500) is "app / best app / free app", meaning people looking to download or choose an app. For an article site that is the competitive, app-store-dominated part. The one clearly informational term, the Notion how-to, is only 1,344/month and falling. ADHD is the only cluster up year on year (+85%), but it is small: 590 to 720 searches per month, and the ADHD numbers are a few bucket steps.

## What I would tell him
- The topic is **falling: Aug-Oct 2026 averaged 14,400 against 18,840 in May-Jul (-24%), and it is 10.8% below Aug-Oct 2025 and 78% below its January peak.**
- The 20% rebound is one month. Wait for Nov and Dec to confirm, and expect a seasonal rise regardless.
- The AI keyword is new and tiny (1,300/month in October, down from 1,900 in spring). Do not size a plan on the percentage.
- **Recommendation:** do not pour content into the head terms now on the strength of these two numbers. If the team still wants to play in this topic, start small and aim for the January window: publish a few pieces in Oct-Nov so they are indexed before the New Year spike, and pick the niche angles (ADHD, Notion how-to, iPhone widget) instead of the head "habit tracker app", which sits in the transactional, app-store-heavy cluster. Re-check the data after the December and January figures arrive. Test the AI angle with at most one piece.

## Limits and not obtained
- Volumes are probably buckets (identical series across variants; steps of about 20-25%), so small percentage moves for single keywords are not findings.
- Only 9 keywords: this is not a full keyword universe, so the 26,500 is the figure for this export, not the whole topic. Round-by-round collection was not done (the user supplied an export).
- Intent labels are word rules plus my reading; nothing was verified against live results.
- The provider's "data available to" date, fetch date and the exact US/English settings are not stated in the file; the last month may be incomplete or revised.
- Demand inside AI assistants, app stores and marketplaces is not in this data, which matters for a topic where people search for apps.
- Searches are not visits: I have not converted these volumes into traffic or revenue.
