---
name: marketing-campaign-brief
description: "Writes or reviews a one-page marketing campaign brief: one measurable objective, one audience, the offer, a channel plan whose budgets add up, a measurement plan and a list of assumptions, with every figure tagged as given, assumed or calculated and a script that checks completeness and arithmetic. Use when the user asks for a campaign brief, a marketing plan for a launch or promotion, a go-to-market one-pager, a channel and budget plan, or a review of an existing brief. Do not use for writing the ads, posts or emails themselves, for keyword research, or for long-range brand strategy."
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only) and makes no network calls. Without Python, add up the channel budgets and scan for untagged figures by hand.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Marketing campaign brief

Turn a loose request ("we need a campaign for the launch") into a page a team can execute and later judge: what success is, for whom, with what money, measured how. A brief full of confident benchmarks nobody supplied is a failed brief, because the team will plan against numbers that came from nowhere.

## Ground rules

1. **One primary objective.** A metric, a baseline, a target and a deadline. Other goals are secondary and cannot override it.
2. **Every figure is tagged.** `[given]` came from the user or their files. `[assumption]` is supplied here and must be confirmed. `[calc]` is derived, with the arithmetic shown. No benchmark (click rate, conversion rate, cost per click, open rate) appears without one of these, and an assumed benchmark is never used silently to "prove" the target is reachable.
3. **Ask before inventing.** If the objective, the budget, the audience or the offer is missing and cannot be inferred from the material, ask up to five questions first. If the user wants a draft anyway, write it with `[assumption]` tags and repeat the questions in the last section.
4. **The money adds up.** Channel budgets plus any reserve equal the total. Every channel has a job, a KPI and a target.
5. **A KPI needs a data source.** If nobody can say where the number will be read, it is not a KPI yet.
6. **Targets, not promises.** No "guaranteed", no "will go viral". State what would make the team stop or shift money.
7. **Claims about the product must be supportable.** Flag any superlative, comparison or health, finance or savings claim in the message for the owner to substantiate.

## Workflow

### 1. Extract what is given

From the request and any files, list: product and price, the business goal behind the campaign, baseline numbers, audience facts, budget, dates, constraints (brand, legal, channels already owned), and past results. Quote figures exactly. Note contradictions in the material (two budgets, two dates) instead of choosing one.

### 2. Close the gaps

Check the list against the nine sections below. For each gap decide: ask (it changes the plan), or assume (it is minor and reversible). Ask the questions in one message, most important first. Do not ask what the material already answers.

### 3. Write the brief

Use this layout and these heading names; the check script reads them.

```
# Campaign brief: <name>

## Objective
Primary objective: <metric> from <baseline> to <target> by <date>. [given|assumption|calc]
Secondary: <at most two>
Why now: <the business reason, one sentence>

## Audience
<One primary segment: who, the situation they are in, what they use today, where they can be reached.>
Not targeting: <who is left out on purpose>

## Offer and message
Offer: <what they get, price or terms, deadline>
Message: <one sentence the audience should remember>
Proof: <facts that support it, each tagged; claims needing substantiation flagged>
Call to action: <one>

## Channel plan
| Channel | Role | Budget | KPI | Target | Owner |
|---|---|---|---|---|---|

## Budget
Total budget: <amount> [given]
<How the split was reasoned; reserve if any; what is excluded (staff time, tools).>

## Measurement
| KPI | Data source | Checked | Decision rule |
<Include the path from channel KPIs to the primary objective, with arithmetic tagged [calc].>

## Timeline
<Dated milestones: assets ready, launch, first review, end, wrap-up.>

## Risks and guardrails
<3 to 5: what could go wrong, the early sign, the response. Legal and brand limits.>

## Assumptions and open questions
<Every [assumption] in the brief, as a list the owner can confirm or correct, then the open questions.>
```

How to reason about channel choice, funnel arithmetic and decision rules is in [references/brief-reasoning.md](references/brief-reasoning.md). Read it when choosing channels or building the path from budget to target.

### 4. Check

```bash
python scripts/brief_check.py brief.md
```

Fix every FAIL (missing section, objective without number or deadline, budgets that do not add up, untagged figure, unlisted assumptions) and consider each WARN. Re-run until clean. Do not edit the script, and do not remove a figure only to pass; tag it honestly.

### 5. Deliver

Give the brief, then three lines:

```
Confirm first: <the 1 to 3 assumptions that would change the plan most>
Check result: <FAIL/WARN counts, or "script not run; totals added by hand">
Not covered: <creative, media buying details, legal review>
```

When reviewing an existing brief, run the script on it as it is, then report: what fails, what is asserted without support, whether the channel KPIs can add up to the objective, and a corrected version only if asked.

## Limits

- The script checks structure and arithmetic. It cannot tell a wise plan from a tidy one.
- The script polices tags on money amounts, percentages and channel targets. Other numbers (counts, durations) follow the same rule but are checked by eye.
- Benchmarks differ by industry, country and season. The skill supplies none as fact; any used are assumptions until the user's own data replaces them.
- A brief is not legal review. Regulated claims, promotions with prizes, and messaging to minors need a qualified reviewer.
- Heading names must match the layout for the script to find sections.
