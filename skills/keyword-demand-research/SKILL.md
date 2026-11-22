---
name: keyword-demand-research
description: Measures search demand for a topic from keyword data - builds the keyword list in rounds, merges close variants so searches are not counted twice, labels search intent, reads trends over fixed windows and reports a de-duplicated total with its limits, using a bundled clustering script. Use when the user asks for keyword research, search volume or demand sizing, keyword clustering, intent classification, "is this topic growing", or which topics to write first from a keyword export or their own keyword-data API. Do not use for auditing a page, writing the article itself, or paid-ads bid planning.
license: Apache-2.0
compatibility: The clustering script needs Python 3.9 or newer (standard library only) and makes no network calls. Keyword data comes from the user's own export or their own API account; the skill ships no credentials. Without Python, apply the clustering rules by hand on the top 50 keywords.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Keyword demand research

Turn a pile of keywords into a demand figure a decision can rest on: one number per real search need, a stated intent, a trend read over named months, and a list of what the data cannot show. A big total built from double-counted variants or off-topic keywords is a failed study.

## Ground rules

1. **Every number comes from a file.** Volumes are read from the user's export or a saved API response, never recalled or estimated. Sums are computed by script. A figure that could not be obtained is written "not obtained".
2. **Count each search need once.** Ad-platform volumes merge close variants ("desk" and "desks" return the same number), so raw sums overstate demand. Report the raw sum and the de-duplicated sum; the de-duplicated one is the working figure.
3. **Say what each number is.** Source, location, date fetched, months covered, and whether it is a monthly average or a single month. Bucketed data is called bucketed.
4. **Classify before you total.** Brand-navigational heads, off-topic meanings of a word and tool-seeking searches are reported in their own rows, not inside the total the user will plan against.
5. **Name the trend window.** "Rising" always carries the two periods compared. One month is never a trend.
6. **The user's account, the user's budget.** API keys are read from the user's own environment or config at run time and are never written into a script, a report or the chat. Set a spend cap before the first paid call.

## Workflow

### 1. Fix the question

Write one line: topic, market (country, language), what decision the number feeds (content plan, market sizing, go/no-go), and the data source. If the user gave an export, go to step 3.

### 2. Collect in rounds (only when pulling from an API)

Read [references/collection-method.md](references/collection-method.md) before writing any collection code. In short: check the balance and the price list, set the cap, expand seeds in rounds, save every raw response, stop when a round adds little new volume.

### 3. Cluster and measure

Put the keywords in one CSV with a `keyword` column and one column per month (headers ending in `YYYY-MM`), then run:

```bash
python scripts/keyword_cluster.py keywords.csv --out clusters.csv --brand "brand one,brand two" --exclude "regex for off-topic meanings"
```

- `--brand`: the user's competitors and other names people search to reach a specific site. These become `navigational-brand` and leave the counted total.
- `--exclude`: a pattern for other meanings of the head word. Excluded clusters stay visible in the report.
- `--rules rules.json` replaces the built-in intent word rules; use it when the niche has its own vocabulary. Do not edit the script to change a label.

The script prints the raw sum, the de-duplicated sum, the counted sum, totals by intent, the total trend and one line per cluster with the rule that merged its variants.

### 4. Read the top by eye

Rules mislabel. Read every cluster that holds more than 2% of the counted total, and at least the top 30:

- Is the merge right? A cluster joined only by "identical series" with unrelated words is split by hand and noted.
- Is the intent right? Fix it in the rules file or with `--brand` / `--exclude`, then re-run. Do not patch numbers in the report.
- Does the word have another meaning (a game, a medical term, a place)? Exclude it.

### 5. Read the trend

Use the script's readings and the rules in [references/trend-reading.md](references/trend-reading.md): last three months against the previous three, the same three months a year earlier, the peak month, and the flags (`one-off-spike`, `one-month-rebound-after-decline`, `new-in-last-12-months`). State the comparison in words: "falling: Aug-Oct against May-Jul, -26%".

### 6. Report

Lead with the working figure and the decision. Use this layout:

```
Question: <topic, market, decision>
Source: <tool or API, endpoint, location, date fetched, months covered>
Working figure: <de-duplicated, counted> searches per month (12-month average); <last month> in <month>
Raw sum for reference: <raw> (<n> keywords in <m> clusters; <x> removed as double counting)
Left out of the total: <brand-navigational: n, volume> <excluded meanings: n, volume> <tool-seeking, if the decision is about articles>
Trend: <label> - <window A> against <window B>, <pct>; peak <month>; flags
Top clusters: <table: cluster, intent, avg, trend, variants>
Recommendation: <what to do first and why, tied to rows of the table>
Limits and not obtained: <bucketed data; rule-based intent; what was not measured>
```

Searches are not visits: never convert volume to traffic or revenue without a stated click-through assumption labelled as an estimate.

## Limits

- The script clusters on spelling and identical monthly series. It does not know meaning: "sofa" and "couch" stay separate, and two unrelated keywords can share a series.
- Intent rules are English word lists. For other languages supply a rules file.
- Keyword tools see search engines only. Demand inside AI assistants, app stores and marketplaces is not in the data; say so when the audience lives there.
- New terms appear in keyword tools with a delay, so a young topic is under-counted.
