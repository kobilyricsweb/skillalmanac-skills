# Plan: measuring US search demand for "home battery storage"

Nothing has been run and no API has been called. This is a plan and a script outline only.

## 0. Things I do not know (check before spending)

- **Which provider?** You said "a keyword-data API" without naming it. I do not know its endpoints, pricing model, or field names. Everything below is written provider-neutral. Before any spend, read its pricing page and note: price per keyword-volume task, price per keyword (or per batch of up to N keywords), price for related-keyword or suggestion endpoints, price for trend and history data, and whether it has a free "account balance" or "usage" call.
- **Where does the volume come from?** Most keyword APIs return Google Ads Keyword Planner volume (rounded, bucketed, and averaged over 12 months). Some return clickstream-modelled volume instead. Find out which one yours is. It changes how much to trust small numbers (see section 6).
- **How is the $40 consumed?** The budget plan assumes cost scales with the number of keywords or tasks. If your provider bills a flat fee per task regardless of keyword count, batching becomes the main lever. If it bills per returned row, related-keyword calls are the expensive ones. The cost table in section 4 uses placeholders (`P_vol`, `P_rel`, `P_trend`) that you fill in from the pricing page.

## 1. What question the study answers

"How many US searches per month are there for home battery storage, and is that demand growing, seasonal, or regional?" For a seller of residential battery systems, that breaks into four measurable parts:

1. **Head term size.** Monthly US volume of "home battery storage" itself.
2. **Cluster size.** Total monthly US volume of the whole topic: all the ways people phrase the same need (home battery, solar battery storage, Powerwall, whole home backup battery, and so on). The head term alone understates demand because searchers split across many wordings.
3. **Trend and seasonality.** 24 to 60 months of monthly history for the head term and the top cluster terms. Look for growth and for peaks around storms, outages, and tax-credit news.
4. **Intent mix.** Which parts of the cluster are people who might buy (cost, installer, quote, near me) and which are curious or researching (how does it work, what is it).

Optional fifth part, only if budget remains: **geography**, meaning state-level volume for the top 3 to 5 terms, since US residential battery demand is very uneven (California, Texas, Florida, Hawaii, and storm and wildfire regions).

## 2. Study design

### Phase A: seed list (free, no API)
Hand-write 25 to 40 seeds across groups:
- Core: home battery storage, home battery, home battery backup, residential battery storage, house battery
- Solar-linked: solar battery storage, solar battery, battery for solar panels, solar plus storage
- Product names: Tesla Powerwall, Enphase battery, LG home battery, Generac PWRcell, Franklin WH, Sonnen, Powerwall alternatives
- Purpose: whole house battery backup, power outage battery, backup power for home, off grid battery
- Commercial intent: home battery cost, home battery installation, home battery installers near me, home battery tax credit, home battery rebate, best home battery
- Informational: how does a home battery work, are home batteries worth it, home battery vs generator, lifespan

Do not include unrelated terms such as car batteries, laptop batteries, or utility-scale storage, except as a short negative-keyword list for filtering later (car, laptop, phone, AA, lithium battery charger, grid scale, utility).

### Phase B: expand with the API (cheap, gated)
Run the provider's related-keyword or suggestion endpoint on a small number of core seeds only (3 to 5), capped to a modest number of results each (for example 200 to 300). Deduplicate, normalise case and whitespace, and drop negative-keyword matches. The goal is a candidate list of roughly 600 to 1,000 phrases.

### Phase C: volume lookup for the full candidate list
One batched volume call per chunk, US only (location = United States, language = English). Collect monthly volume, and if returned: competition, CPC, and the 12-month monthly series.

### Phase D: trend history for a short list
Take the top 10 to 20 terms by volume plus the head term. Pull the longest history available (24 to 60 months). This is the one step where cost per keyword might be higher, so keep the list short.

### Phase E: optional geography
Only for the top 3 to 5 terms, by state (50 states + DC). Run only if the provider prices location as separate tasks and the remaining budget covers it. This is the first thing to cut.

## 3. Budget ($40)

Hold back 20 percent ($8) as reserve for retries, errors, and one follow-up question. That leaves $32 to plan against. Fill the table after reading the pricing page.

| Phase | Call volume (planned) | Unit price | Planned cost | Cut order |
|---|---|---|---|---|
| A seeds | none | $0 | $0 | n/a |
| B expansion | 3 to 5 calls | `P_rel` | at most about $4 | reduce number of seeds |
| C volume | about 1,000 keywords in batches | `P_vol` | at most about $10 | reduce candidate list to top 500 |
| D history | 20 keywords | `P_trend` | at most about $4 | reduce to 10 keywords |
| E geography | 5 terms x 51 locations, or provider equivalent | `P_geo` | at most about $10 | skip |
| Reserve | | | $8 | never spend before A to D are checked |

Rules:
- **Dry-run estimate first.** The script computes a projected cost from the unit prices and the number of requests, prints it, and refuses to run if the projection exceeds the phase cap. It never calls the API during this step.
- **Pilot before scale.** For each phase, first send exactly one small request (1 task, 5 to 10 keywords). Check the real charge against the projection (read the balance before and after, or use the cost field in the response). Only then run the rest. If actual cost is more than 1.5 times the projection, stop and re-plan.
- **Hard stop.** Track cumulative spend from the cost field returned in each response (not from my estimate). Abort when cumulative spend reaches $32.
- **No retries of paid calls without a check.** A timeout may still have been billed. On error, check the balance or task list before resending.

## 4. Script outline (Python, not yet written or run)

```
config.py
  API_KEY from environment variable (never in the file)
  LOCATION = "United States", LANGUAGE = "English"
  BUDGET_TOTAL = 40.0; RESERVE = 8.0; PHASE_CAPS = {...}
  PRICES = {"vol": P_vol, "rel": P_rel, "trend": P_trend, "geo": P_geo}   # filled from pricing page
  NEGATIVES = [...]
  DRY_RUN = True            # default; must be flipped on purpose

seeds.py          # the Phase A list, plain text, one per line

client.py
  call(endpoint, payload) -> (response, cost)
    - writes every request payload and raw response to raw/<phase>_<n>.json BEFORE any parsing
    - reads the cost from the response; adds to ledger
    - if DRY_RUN: returns projected cost, makes no network call
    - timeout and 429 handling: wait, then check balance before any resend

ledger.py
  append-only spend.csv: timestamp, phase, endpoint, n_keywords, cost, cumulative
  assert_within_budget(projected) -> raises if cumulative + projected > limit

clean.py
  normalise(kw): lowercase, strip, collapse spaces
  is_relevant(kw): no negative term; contains a topic word (battery, powerwall, storage, backup)
  dedupe, keep source seed for each candidate

phase_b_expand.py   # related keywords for 3 to 5 seeds -> candidates.csv
phase_c_volume.py   # batched volume -> volumes.csv (kw, volume, cpc, competition, monthly series)
phase_d_trend.py    # history for top 20 -> trend.csv
phase_e_geo.py      # optional

analyze.py
  head_term_volume
  cluster_total = sum of volume over deduplicated relevant keywords (see caveat 6.2)
  intent buckets by modifier regex (cost|price|install|near me|quote|rebate|credit = commercial;
      how|what|why|vs|worth = informational; brand names = brand)
  seasonality index per month = month volume / yearly mean; YoY change
  output: summary.md plus 3 charts (top terms, intent split, monthly trend)

main.py
  python main.py --phase B --dry-run     # prints projected cost, makes no call
  python main.py --phase B --pilot       # one small paid request
  python main.py --phase B               # full phase, only after pilot cost verified
```

Design points: raw responses saved first so nothing paid is ever lost; resumable (skip keywords already in volumes.csv); one phase per invocation so spend is always a deliberate choice.

## 5. Outputs

- `summary.md`: head-term volume, cluster total with range, top 25 terms, intent split, trend and seasonality, and caveats.
- `volumes.csv`, `trend.csv`, `candidates.csv`, `spend.csv`, plus the saved raw JSON.
- A one-paragraph answer in plain words, for example "about X searches a month for the head term, about Y for the topic as a whole, growing or flat by Z percent, peaking in month M".

## 6. Pitfalls to handle explicitly

1. **Rounded and bucketed volume.** Keyword Planner style data is rounded and low-volume terms may show as 0 or 10. Treat anything under about 50 as "unreliable, directional only".
2. **Cluster totals double count.** A search for "home battery" and one for "home battery storage" are different queries, but near-duplicates and sub-phrases share searchers in some tools. Report the cluster total as a range (head terms only versus everything) and say it is not unique searchers.
3. **Grouped variants.** Some APIs merge close variants (plural, word order), so "home battery storage" and "home storage battery" may return identical numbers. Do not add them as if they were independent. Detect identical volume series on near-duplicate strings and keep one.
4. **12-month average hides seasonality.** Use the monthly series, not the headline number, for any statement about timing.
5. **Brand and off-topic noise.** "Powerwall" volume includes people who are not shopping. Keep brand terms in their own bucket instead of the headline.
6. **Policy-driven spikes.** US federal tax-credit news and big storms move this topic. Annotate spikes instead of treating them as trend.
7. **Search volume is not buyers.** It measures interest, not leads. Convert with your own conversion rate if you want a revenue estimate, and label that as an assumption.
8. **Location.** Confirm the API's "United States" setting is country-level and not some default region.

## 7. Order of work

1. Read provider pricing and fill `PRICES`; confirm the data source (section 0). No spend.
2. Write seeds; write script; run every phase with `--dry-run` to view projected costs. No spend.
3. Pilot Phase B (one call), compare actual and projected cost.
4. Run B, review candidates by hand (drop junk), then pilot and run C, then D.
5. Decide on E from the remaining balance.
6. Run `analyze.py`, write `summary.md`.

Expected total spend if prices are typical: about $15 to $25 of the $40, leaving the reserve untouched. This is an estimate and cannot be confirmed until the real price list is known.
