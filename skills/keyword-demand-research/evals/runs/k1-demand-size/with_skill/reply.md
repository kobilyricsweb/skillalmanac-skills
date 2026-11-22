# Standing-desk search demand: size and first five articles

**Question:** Search demand for "standing desk" topics, US, Google Ads monthly volumes; decision: which articles to write first for a store that competes with IKEA, Uplift and Flexispot.

**Source:** your export `k1_standing_desk_keywords.csv` (36 keywords, 15 months, 2025-08 to 2026-10, US). Fetch date not stated in the file. Volumes look bucketed (many variants share one number, and "standing desk" reads exactly 60,500 in all 15 months). Averages below are for the latest 12 months (2025-11 to 2026-10). Clustering by `keyword_cluster.py` (output in `clusters.csv`, console log in `run.txt`), then read by eye.

## Working figure

**About 130,400 searches per month** that articles can target (12-month average, de-duplicated, brand names and other meanings removed). October 2026 alone: 121,840.

| Figure | Searches/month |
|---|---|
| Raw sum of all 36 keywords | 334,477 |
| De-duplicated (one per search need, 24 clusters) | 175,710 |
| Counted (script): minus brand and excluded | **130,410** in 19 clusters |
| My adjusted counted figure (see below) | about 125,700 |
| Same, without the bare head "standing desk" | about 65,200 |

Double counting removed: 158,767 (47% of the raw sum). Raw sum is shown for reference only; do not plan against it.

Adjustments I made after reading the clusters (not patched into the script output):
- "standing desk black friday" averages 3,317 only because of one month (Nov 2025 = 33,100, Dec 1,900; the other months are 480). Without that spike it is about 480. Possible season, one cycle seen. Nov 2026 is not in the data.
- "standing desk height calculator" (1,900) is a tool-seeking search (the script labelled it transactional by mistake). It wants a calculator, not an article, so I took it out of the article total.
- The head term "standing desk" (60,500) is 46% of the counted total. Its intent is mixed (shoppers, category pages, definitions) and it is dominated by store category pages. It is real demand but not a first-article target.

## Left out of the total

| Group | Keywords | Searches/month |
|---|---|---|
| Brand-navigational: uplift desk (22,200), ikea standing desk (14,800), flexispot standing desk (5,400) | 5 | 42,400 |
| Other meanings: "tiny desk standing room tickets" (1,300; concert), "desk standing fan" (1,600; fans) | 2 | 2,900 |
| Tool-seeking: standing desk height calculator | 1 | 1,900 |

The brand rows are people looking for a competitor's site. You cannot capture them with articles; the useful move is comparison content ("Uplift vs ..."), but this export has no "vs" or "alternative" keywords, so that demand is **not obtained**.

## Trend

Total counted demand: **flat**. August to October 2026 against May to July: -1.9%. Against August to October 2025: -9.7%. Peak was November 2025 (168,460, inflated by the Black Friday spike and by electric desks peaking); October 2026 is 28% below it. Most big clusters are exactly flat, so the movement comes from a few clusters:

- Falling: electric standing desk, 12,100 / 9,900 / 8,100 in May to July against 6,600 / 5,400 / 6,600 in Aug to Oct 2026 (-38%; -68% on a year ago; peak 27,100 in Dec 2025). October rose from 5,400 to 6,600: one month, not a trend; November would confirm it. "Standing desk work from home" falls steadily, 8,100 (Aug 2025) to 1,900 (Oct 2026), -29% on the 3-month read.
- Rising: walking pad for standing desk, 590 (Aug 2025) to 5,400 (Oct 2026), up in 14 of 14 monthly steps, +60% Aug-Oct against May-Jul, about 7.5 times a year ago. How to use a standing desk: +20% on the 3-month read (880 to 1,900 over 15 months). Standing desk for VR: new in the last 12 months (0 until Feb 2026, 720 in Oct), tiny base.

## Top clusters (12-month average)

| Cluster | Intent (my read) | Avg/month | Trend (Aug-Oct vs May-Jul) | Variants |
|---|---|---|---|---|
| standing desk | mixed head | 60,500 | flat | 2 |
| uplift desk | brand | 22,200 | flat | 2 |
| ikea standing desk | brand | 14,800 | flat | 1 |
| electric standing desk | commercial | 14,267 | falling -38% | 3 |
| adjustable height desk | commercial | 12,100 | flat | 3 |
| best standing desk | commercial | 9,900 | flat | 3 |
| standing desk converter | commercial | 6,600 | flat | 2 |
| flexispot standing desk | brand | 5,400 | flat | 1 |
| standing desk mat | accessory, commercial | 4,400 | flat | 2 |
| standing desk work from home | informational | 3,825 | falling -29% | 1 |
| standing desk chair | accessory, commercial | 3,600 | flat | 1 |
| standing desk benefits | informational | 2,900 | flat | 3 |
| walking pad for standing desk | commercial | 2,542 (5,400 now) | rising +60% | 1 |
| how to use a standing desk | informational | 1,400 (1,900 now) | rising +20% | 1 |

Merge checks: "adjustable height desk / height adjustable desk / adjustable height desks" merged on identical series and the same words, which is right. "standing desk benefits / benefits of standing desk / benefits of a standing desk" and "best standing desk / standing desk best" also merge correctly. Intent labels for most clusters came back "unclassified" from the script's word rules; the intent column above is my reading by eye, not script output.

## Recommendation: write these 5 first

1. **Best standing desk** (9,900, flat, 3 variants). Highest-value commercial cluster you can target that is not the head. It is where IKEA, Uplift and Flexispot get compared, so write it as a tested buyer's guide that includes your own models next to theirs.
2. **Walking pad for standing desk** (5,400 in Oct 2026 and rising every month for 14 months). The only large cluster with sustained growth, so the article earns more each month it is live. Risk: the topic is young and a keyword tool lags; confirm you sell or can recommend compatible products.
3. **Adjustable height desk** (12,100, flat). Second-biggest article-addressable cluster; the same buyer under a different name, and a chance to rank for it without Uplift or IKEA being the obvious brand answer. Cover it as a related guide, cross-linked to #1, rather than a duplicate.
4. **Standing desk converter** (6,600, flat). A distinct product need (a riser on an existing desk), a buyer who may not buy a full desk from you. Only worth it if you stock converters.
5. **Standing desk benefits** (2,900, flat, 3 variants). Smaller, informational and easier to rank than the product topics; it feeds the buyer guides. If you want growth over size, swap in "how to use a standing desk" (1,900 and rising).

Not first, and why: the head "standing desk" (60,500) is a category page job, not an article; "electric standing desk" (6,600 now, down from 27,100) is falling, so write it only after #1 as a shorter explainer; "work from home" is falling; brand rows are not targetable; mats and chairs (4,400, 3,600) are accessory articles for a second wave; Black Friday (480 normally, one 33,100 month) needs a seasonal page ready before November, decide after seeing November 2026.

## Limits and not obtained

- Volumes are bucketed Google Ads figures, so small moves (for example 880 to 1,000) are one bucket step, not a finding. Every flat series with exactly the same number for 15 months should be read as "no visible change within the bucket".
- Intent is rule-based plus my reading; no search results were checked, so I cannot say how hard any term is to rank for.
- Demand inside AI assistants, YouTube, Amazon and Reddit is not in this data.
- "Vs" and "alternative" searches for IKEA, Uplift and Flexispot, difficulty, and click-through are not in the export. Searches are not visits: no traffic or revenue is estimated here.
- Black Friday is one cycle only; a season cannot be confirmed.
- The export's fetch date and the provider's "data available to" date were not given; October 2026 may be revised.
