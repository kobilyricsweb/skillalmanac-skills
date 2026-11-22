# Plan: US search demand for "home battery storage"

Nothing has been run and no API was called. This is a plan and a script outline only.

## 1. The question (one line)

Topic: home battery storage (residential battery systems). Market: United States, English. Decision: content plan and market sizing for a seller of residential battery systems (which topics to cover first, and how big the search pool is). Source: the user's own keyword-data API account, $40 credit. The provider is not named, so endpoint names below are generic and must be mapped to the real provider's endpoints.

## 2. What I still need from you (unknowns, not guessed)

- Which provider, and the name of the environment variable or config file holding the key. The key is read at run time and never written into the script, logs, saved responses or the report. Do not paste it into chat.
- Unit prices per endpoint. They are not known to me. Step A reads them from the provider's free account endpoint; every cost below is a formula, not a quote.
- Your own brand and your main competitors (for the brand-navigational list).
- Whether you also want "home battery backup" and "solar battery" treated as in scope (see seeds).

## 3. Budget and spend cap

- Credit: $40. Default cap with no other instruction: the lower of a fixed amount you name and 50% of the current balance. Proposed cap: **$20** (50% of $40), leaving $20 for a re-run or a second source. Tell me if you want a different cap.
- The code checks the running total before every paid call and stops at the cap.
- Every call is logged to a ledger. The final spend is the ledger sum, checked against the balance difference.
- Before spending, I show the per-round call-count x unit-price estimate and wait for your yes.

## 4. Pre-flight (free calls only)

1. Read the key from the environment. Call the free account endpoint: record balance and each endpoint's unit price.
2. Compute the dry estimate per round (below). Show it. Get a yes.
3. Create folders: raw/ (every raw response, saved before parsing, named after the call), ledger.csv, failed/ (failed responses under a different name, never parsed).
4. Re-runs read saved raw files instead of paying again.

## 5. Collection rounds

Each number must record: endpoint, location (US), language (English), date range, and whether the provider buckets or models the value.

| Round | Pull | Notes |
|---|---|---|
| 1 | Suggestions for 20-50 seeds | Seeds: home battery storage, home battery, home battery system, residential battery storage, home energy storage, home battery backup, solar battery storage, solar battery, whole house battery, battery backup for home. Product names: Tesla Powerwall, Enphase IQ battery, Franklin WH, LG/other residential batteries, Generac PWRcell, Sonnen. Your own phrasing. Singular and plural of each head. |
| 2 | Next pages for seeds that hit the page limit; modifier seeds; related-keyword/keyword-idea endpoints on the heads | Modifiers: best, vs, cost, price, how much, how long does it last, how it works, installation, tax credit, rebate, incentive, for solar, near me, by state (California, Texas, Florida etc.), lithium vs lead acid, outage/blackout. |
| 3 | Bare ambiguous heads, filtered to the intended meaning; ranking keywords of 1-2 main competitor sites | Ambiguous: "battery storage" alone (utility-scale, grid), "powerwall", "generator". Filter with a pattern keeping only home/residential meaning. |
| Volume pass | Authoritative monthly volumes for the kept list, US, at least 13 months, 15 if I want a year-on-year three-month window | One consistent source for the totals. I will ask for 15 months. |

Stop rule: after each round count keywords first seen in that round and their volume. Stop when new volume is mostly close variants of what is held, or under about 15% of the list's volume. Per-round numbers go in the report as evidence. The list stays a lower bound.

Dry estimate formula (fill in after step 4.1):
- Round 1: (number of seeds / seeds per call) x suggestion unit price
- Round 2: (pages + modifier seeds + related-keyword calls) x unit prices
- Round 3: (filtered head calls + competitor ranking calls) x unit prices
- Volume pass: (kept keywords / keywords per call) x volume unit price, the likely largest line item. Run it last, on the de-duplicated kept list only, to avoid paying volume for junk.
- Optional cross-check (only if the cap leaves room): second volume source on the top 100 keywords; live results pages for the 20-30 largest heads; the provider's keyword difficulty (named as that provider's metric).

If the volume pass does not fit under the cap, I trim the long tail (lowest-volume keywords by suggestion-stage figures) and report how many keywords went unmeasured under "not obtained".

## 6. Classification pass

- Brand-navigational (`--brand`): your competitors and names people search to reach a site: tesla powerwall, enphase, sonnen, generac, sunrun, sunpower, lg chem, franklinwh, plus your own brand. They become `navigational-brand` and leave the counted total. (A generic product like "powerwall" is brand-navigational; I will report it in its own row.)
- Excluded meanings (`--exclude`): utility-scale or grid battery storage, car/EV/phone/laptop battery, UPS for computers, "battery storage" in other senses, jobs/careers, stock tickers. Excluded clusters stay visible in the report.
- Tool-seeking (calculators, sizing tools): reported separately, since the decision is about articles.
- Ambiguous group for keywords that probably belong but cannot be proven from the text; reported separately.
- Intent: built-in rules first, then a custom rules.json for this niche (cost, install, rebate, tax credit, vs, near me, kWh, backup, off-grid). The script is not edited to change a label.
- Keywords the volume endpoint rejects or returns empty are counted and listed as "not obtained".

## 7. Cluster and measure

Build `keywords.csv` with a `keyword` column and one column per month, headers ending `YYYY-MM`, then (to be run later, not now):

```
python <local-path> keywords.csv --out clusters.csv --brand "tesla,powerwall,enphase,sonnen,generac,sunrun,sunpower,franklinwh,<your brand>" --exclude "<regex for utility-scale, EV, phone, UPS, jobs>" [--rules rules.json]
```

The brand and exclude lists are drafts and will be adjusted after reading the output. It prints the raw sum, de-duplicated sum, counted sum, totals by intent, total trend and per-cluster merge rules.

Then I read by eye: every cluster over 2% of the counted total and at least the top 30. Check merges (clusters joined only by "identical series" with unrelated words get split by hand and noted), check intent (fix by rules/flags and re-run, never patch numbers), check other meanings. "Home battery" and "solar battery" may be the same need to a buyer but the script will not merge them; I note it rather than merge by hand silently.

## 8. Trend reading

Per trend-reading rules, with months named: last 3 months vs previous 3; year on year (last 3 vs same 3 a year earlier with 15 months); distance from peak and the peak month; 12-month average and last month. Labels: rising above +15%, falling below -15%, flat between. Check flags `one-off-spike` (give the average with and without the month), `one-month-rebound-after-decline`, `new-in-last-12-months`. Expect season (heat waves, hurricane season, winter storms, tax-credit news): with under 24 months say "possible season, one cycle seen". Note the provider's "data available to" date because the last month may be incomplete. Tax-credit and policy news can create spikes, so the biggest clusters are read individually.

## 9. Outline of the collection script (collect.py, to be written after your yes)

```python
# Outline only. Not run. Provider endpoints are placeholders.
import os, json, time, csv, pathlib

CAP_USD = 20.00                       # agreed with user
KEY = os.environ["KEYWORD_API_KEY"]    # name confirmed with user; never printed or logged
RAW, FAILED = pathlib.Path("raw"), pathlib.Path("failed")
LEDGER = "ledger.csv"                  # time, endpoint, file, cost, status
spent = 0.0

def paid_call(endpoint, params, name):
    global spent
    f = RAW / f"{name}.json"
    if f.exists():                     # re-run reads saved file, no charge
        return json.loads(f.read_text())
    price = PRICES[endpoint]           # read from free account endpoint
    if spent + price > CAP_USD:
        raise SystemExit("cap reached")
    for attempt in range(3):           # retry transient errors with a pause
        resp = http_post(endpoint, params, KEY)   # key sent in header only
        if resp.ok:
            f.write_text(resp.text)    # save BEFORE parsing
            spent += resp.cost; log(endpoint, f, resp.cost, "ok")
            return json.loads(resp.text)
        (FAILED / f"{name}_try{attempt}.json").write_text(resp.text)
        time.sleep(5 * (attempt + 1))
    log(endpoint, None, 0, "failed")

def check_balance_and_prices(): ...    # free call; writes balance + price list

def round1(seeds): ...                 # suggestions for each seed
def round2(seeds, modifiers): ...      # pages, modifiers, related keywords
def round3(ambiguous_heads, competitors): ...  # filtered heads, competitor ranking keywords
def new_volume_report(round_no): ...   # first-seen count and volume; apply the 15% stop rule
def volume_pass(kept_keywords): ...    # US, 15 months, batched
def classify(keywords): ...            # rules: target / brand / adjacent / drop / ambiguous
def write_keywords_csv(): ...          # keyword, YYYY-MM columns
def reconcile_spend(): ...             # ledger sum vs balance difference
```

Steps in order: check_balance_and_prices -> show estimate, wait for yes -> round1 -> new_volume_report -> round2 -> new_volume_report -> round3 -> new_volume_report -> classify -> volume_pass on the kept list -> write_keywords_csv -> keyword_cluster.py -> manual review -> reconcile_spend.

## 10. Report format (final deliverable)

```
Question: home battery storage, US/English, content plan and market sizing
Source: <provider, endpoints, US, date fetched, months covered>
Working figure: <de-duplicated, counted> searches per month (12-month average); <last month> in <month>
Raw sum for reference: <raw> (<n> keywords in <m> clusters; <x> removed as double counting)
Left out of the total: brand-navigational (n, volume); excluded meanings (n, volume); tool-seeking (n, volume); ambiguous (n, volume); not obtained (n)
Trend: <label> - <window A> against <window B>, <pct>; peak <month>; flags
Top clusters: table (cluster, intent, avg, trend, variants)
Recommendation: what to write first, tied to table rows
Per-round collection numbers and spend (ledger sum vs balance difference)
Limits and not obtained
```

Searches are not visits. No traffic or revenue figure appears unless I state a click-through assumption labelled as an estimate.

## 11. Limits to state up front

- Keyword tools see search engines only. Part of this audience asks AI assistants and installer/marketplace sites, and that demand is not in the data.
- Clustering works on spelling and identical monthly series, not meaning ("home battery" vs "house battery" will not merge automatically). Intent labels are rule-based English word lists.
- The list is a lower bound: new terms appear in keyword tools with a delay, and the budget limits the long tail.
- Provider volumes may be bucketed or modelled; I will say which once the provider is known. Small single-keyword moves are not reported as findings.
- Whether $20 (or $40) covers the volume pass is unknown until unit prices are read. The plan trims the tail rather than overspending.

## 12. Next step

Reply with: provider and key variable name, your brand/competitors, and cap confirmation. Then I read the free balance and price list, show the dry estimate, and wait for your yes before any paid call.
