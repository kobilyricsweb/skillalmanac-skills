# Review of "Q1 demand push (v3 - for CEO sign-off)"

Not ready for the CEO. The budget does not add up, the 500-lead objective is not reachable on the brief's own numbers, and the message makes claims nobody has supported. The check script reports 13 FAIL and 5 WARN (run as-is on c2_existing_brief.md; exit code 1 means FAIL). The script does not catch the substantive problems below, which are the ones the CEO will care about.

## 1. The money does not add up

- Channel budgets: $12,000 + $8,000 + $6,500 + $4,000 = **$30,500**. The stated total is **$28,000**. Gap: $2,500 over. There is no reserve row and no note on what the total includes (media only? production, tools, staff time?).
- The podcast line ($6,500, about 21% of the real total) has no KPI and no target. It is the largest unmeasured spend in the plan.

## 2. The leads target cannot be reached on the brief's own numbers

The objective is 500 leads. The channel targets are:

- Paid search: 300 leads for $12,000
- LinkedIn: 150 leads for $8,000
- Webinar: 400 **registrations** (not leads), $4,000
- Podcast: no target

Lead targets from the two paid channels sum to **450**, short of 500 before any other channel is counted. The webinar figure is registrations, a different unit; counting it as leads would double the apparent result.

The Measurement line gives the only arithmetic-like assumptions: CPC $4 and landing-page conversion 2%. Applying them (arithmetic tagged [calc] here, but the inputs are untagged):

- Search: $12,000 / $4 = 3,000 clicks x 2% = **60 leads**, about $200 per lead. The 300-lead target needs 10% conversion, or $40 per lead.
- LinkedIn: $8,000 / $4 = 2,000 clicks x 2% = **40 leads**. The brief does not say whether the $4 CPC applies to LinkedIn at all, which is unlikely to be the same figure across platforms.
- Total from the two paid channels under these assumptions: about **100 leads** against 500. Shortfall about 400.

The 4.5% CTR is described as an "industry average" but is not used in the arithmetic, and it has no source. An unsourced benchmark cannot make the target look reachable.

The brief does not show the path from budget to objective. Per the skill's own reasoning, that path is required, with each step tagged.

## 3. Objective

- Two primary goals: "increase brand awareness" and "drive 500 leads". The skill allows one primary objective; awareness has no metric, no baseline and no target anywhere in the brief.
- No baseline for leads. No firm deadline beyond "Q1" (no day date).
- The objective's 500 leads is not reconciled with any channel plan (see section 2).

## 4. Claims that need substantiation or removal before a CEO sees them

- "The #1 scheduling tool": superlative, no source.
- "Cuts no-shows in half": outcome claim, no source or study.
- "Guaranteed 3x ROAS": a guarantee is not a target, and it is a commitment the company may not be able to keep. A 3x ROAS on $28,000 means $84,000 revenue, but the brief gives no price, order value or revenue figure to test this against. Remove "guaranteed" and state the revenue assumption as [assumption].

## 5. Offer and message

- No offer is stated: no price, terms or deadline. The "Offer:" line is missing.
- No "Proof:" line, so the claims above are unsupported.
- The message is three claims in one line, not one sentence the audience should remember.
- Three calls to action ("Book a demo / Start free / Download the guide"). The skill allows one.

## 6. Audience

- Two segments: SMB owners 25 to 60 in the US and UK, plus enterprise ops leaders. The skill calls for one segment, named by situation, not demographics.
- No "Not targeting" line.
- No reason given for the US and UK split or the channel mix against each market.

## 7. Channels

- Podcast: role "Awareness", no KPI, no target (see section 1 and 3).
- Webinar: role "Leads", but its KPI is "Registrations". Mismatch with the objective's metric.
- Paid search and LinkedIn both claim "Leads" with no stated split of the 500 target between them and no conversion assumptions per channel.
- No budget split reasoning. No reserve. Nothing on why these four channels.

## 8. Measurement

- "We will track performance in the dashboard" names no data source. The skill requires a source for every KPI.
- No measurement table, no "Checked" column, no decision rule. Nothing says what would make the team stop or shift money.
- The assumptions are in one sentence and not tagged.

## 9. Timeline

- "Launch in January, wrap in March": no dates, no year, no milestones (assets ready, first review). Given the date (November 2026), Q1 would be January to March 2027, but the brief should say so.

## 10. Risks and guardrails; assumptions and open questions

- Both sections are missing. The brief has no risks, no legal or brand guardrails, and no list of assumptions for the owner to confirm. The regulated-claim issues in section 4 need legal review before anything goes out.

## What the CEO should confirm first

1. Is the target 500 leads or 500 registrations and leads combined? Is there a second target for awareness?
2. Is the total $28,000 or $30,500? What does the total include?
3. What is the real CPC and landing-page conversion for search and for LinkedIn, and where did the 4.5% CTR come from?
4. Does the "guaranteed 3x ROAS" have an actual revenue basis? If not, remove it.

## Not covered by this review

Creative, media buying details, the legal review of claims, and whether the podcast or webinar is a good use of money. The check script checks structure and arithmetic only.

## Corrected version

Not written, because the skill's review mode asks for one only on request.
