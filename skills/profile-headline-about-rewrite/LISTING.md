# profile-headline-about-rewrite

## One line

Turns a short list of your own job facts into three profile headline options and a five-paragraph About section, with a trace table that ties every number and employer back to a fact you supplied.

## What it does

The skill runs a fixed intake form first. It asks for your role title, employer, team scope, the tools you used, three outcomes (each with a result and, where you have one, a number), your intended audience and up to fifteen keywords copied from one job posting. It then builds a numbered fact register, keeps only the keywords that a fact supports, and writes headlines from three formulas. The About section follows a set paragraph order: who you are, three outcome paragraphs, then one closing sentence. Before anything is delivered, a trace table checks every number, employer, title, date and tool name in the output against the register. Any row that does not match is removed or raised as a question.

## When to use

Use it when a profile headline or About section reads vaguely and you have concrete results to add, for example a reconciliation that now runs in two hours instead of nine, or a dashboard that replaced fourteen static reports. It also helps when you want to see which keywords from a posting you can honestly use, and which ones you cannot.

## When not to use

Do not use it for a full resume, a cover letter, a search strategy or interview preparation. It will not invent achievements, and it stops when fewer than two of your three outcomes have a stated result.

## Requirements

Any text-capable agent that can follow a Markdown procedure. No scripts, no network access and no extra packages. You need your own facts; the skill does not browse for them.

## Example

Excerpt from the smoke run (fixtures/smoke_output.md, produced by following SKILL.md on fixtures/smoke_facts.md):

```
## Keywords
Kept: SQL, Python, dashboards, cohort analysis
Dropped: stakeholder reporting (no fact supports it), forecasting (no fact supports it)

## Headline options
1. Data Analyst | SQL and Python | Cut weekly sales close from 9 hours to 2 hours
2. Data Analyst for hiring managers in retail and e-commerce, automating weekly sales reconciliation
3. Data Analyst with dashboards, lifting retention by 4 points
```

## Limits

The skill does not know the character limit of your platform; check it yourself before choosing a headline. The length targets (120 to 200 words for the About section, 120 characters per headline, 25 words per sentence) are working values for drafting, not published standards. The skill cannot judge whether an outcome is significant, only whether it is stated and traceable. A keyword that a fact supports can still be a weak fit for the job, so review the keyword list yourself.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
