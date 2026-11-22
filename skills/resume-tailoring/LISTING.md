## תקציר

- תוכן עמוד ה-skill: מתאים קורות חיים קיימים למודעת דרושים בלי להמציא ניסיון.
- מחזיר גם רשימת פערים: דרישות במודעה שקורות החיים לא מכסים בכנות.
- כולל script שבודק שלא נוסף מספר, כלי או תעודה שלא היו במקור. בלי רשת.
- אין הבטחה לעבור מערכת סינון (ATS) או לקבל ראיון.
- טיוטה: לא לפרסום לפני סקירה אנושית ותיקון חולשת 'זהירות יתר'.

---

# Listing page content: resume-tailoring

**One line:** Fit the resume you already have to one job posting, without adding a single thing you cannot back up in an interview.

## What it does

You give it your resume and a job ad. It works out which of the ad's requirements your resume already shows, which it shows in other words, and which it does not show at all. It then reorders and rewords what is already there, using the ad's terms only where you really have the thing, and lists the rest as gaps with an honest way to handle each. A script compares the new version with your original and stops on any new number, tool or credential.

## Capabilities

- A tailored resume in plain single-column text with standard headings.
- A gap list: requirements the resume cannot honestly cover, each with a next step.
- `resume_check.py match`: which terms from the posting the resume contains.
- `resume_check.py compare`: flags new numbers, skills copied in from the posting, lost dates, tables, pronouns, over-long bullets.
- Layout and wording rules for resumes that people and parsing software can both read.

## When to use

You have a resume and a specific job ad; you are changing field and need your real experience described in the new field's words; you want to know which keywords you are missing and whether you can honestly add them.

## When not to use

Cover letters, interview practice, profile pages, writing a resume with no source facts, or any request to add experience you do not have.

## Before and after (from saved test runs)

**Without the skill.** Asked to "add whatever keywords it needs" for a financial analyst job, the plain assistant kept the bullets but wrote a summary claiming "a record of speeding up month-end close" and experience "explaining financial results to department heads". The original says only that the candidate was part of the team that shortened the close and that a report was sent to department heads.

**With the skill.** With the skill the resume gained the posting's words for things the candidate really does (variance report, month-end close, budget support) and nothing else. The reply listed Power BI, SQL, CPA and forecasting models as gaps that were not added, and why.

## Requirements

Python 3.9 or newer for the script (standard library only). No network access. English wording is assumed by the script.

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved test runs)

1. Prompt: "Tailor my resume to this job posting." Result: `evals/runs/r1-retail-to-customer-success/with_skill/`. 6 of 6 assertions; the blind grader preferred it (7 against 6) because the other version claimed "customer onboarding" the candidate never did.
2. Prompt: "Here's my resume and a job ad. Optimize the resume so I get the interview - add whatever keywords it needs." Result: `evals/runs/r2-accountant-to-fpa/with_skill/`. 6 of 6; no unbacked keyword added; gaps listed.

## Limits

- It tailors lightly. In one of three test tasks the grader preferred the plain assistant because it translated more real experience into the posting's words.
- The script compares words and numbers; it cannot see an inflated verb or a widened scope.
- Term extraction is for English postings and includes noise such as the company name.
- No screening system is simulated and no result is promised.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Blind grader: with skill preferred in 2 of 3, baseline preferred in 1. Static check: 0 fails. Token overhead about +8%. Not tested: other tools, real triggering, repeated runs, human review.

## Demo script (60 to 90 seconds)

1. Show the retail resume and the customer-success ad side by side.
2. Plain assistant: point at "Customer onboarding and training" in its skills line, which the original never says.
3. With the skill: run `match` (missing: Salesforce, Zendesk, SQL), then the tailored resume, then `compare`: RESULT PASS.
4. End on the gap list: three missing requirements, one honest step for each.

## FAQ seeds

- Will this get my resume past an ATS? It follows layout rules that avoid common parsing failures. It makes no promise about any system.
- Will it add keywords I do not have? No. They are listed as gaps. If you tell it you do have one, it adds it and records your statement.
- Does my resume leave my computer? The skill and its script use no network. What the assistant itself sends depends on the tool you run it in.
- Can it write a resume from nothing? No. It needs your existing resume or your facts.
- Does it work for a CV outside the US? The rules are general; local conventions (photo, date of birth) are not covered.
- Can it make a Word or PDF file? It produces text. Styling is a separate step that should keep one column.

## Changelog

- 0.1.0 (2026-11-20): first version, batch 01.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
