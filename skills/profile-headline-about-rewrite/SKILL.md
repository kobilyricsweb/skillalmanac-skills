---
name: profile-headline-about-rewrite
description: Rewrites a professional profile headline and About section from facts the user supplies, using a fixed intake form, headline and About formulas, a keyword placement rule and a trace table that ties every number, employer and title to a user-given fact. Use when the user wants a vague profile headline or About text sharpened, or asks for a profile rewrite built only from their own achievements. Do not use for writing a full resume, a cover letter, a job search plan, or for inventing achievements the user did not state.
license: Apache-2.0
compatibility: Requires nothing beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Profile headline and About rewrite

Use this procedure to turn a short set of user facts into three headline options and one About section. Every number, employer, job title, date and tool name in the output must trace to a fact the user supplied. If the facts are too thin, stop and ask instead of padding.

## Inputs: fact-intake form

Ask the user for these fields. Accept short answers. Do not invent missing values.

| Field | Required | Format |
|---|---|---|
| F1 Role title | yes | Title as the employer uses it |
| F2 Employer | yes | Employer name, or "self-employed" |
| F3 Scope | yes | Team size, users served, budget or data volume, as numbers where known |
| F4 Tools and methods | yes | Up to 6 named tools or methods the user used |
| F5 to F7 Outcomes | yes, 3 | Each: action, result, number (or "no number") |
| F8 Audience | yes | Who reads it, for example hiring managers in one industry |
| F9 Target keywords | no | Up to 15 keywords copied from one job posting |

## Workflow

1. Intake check. Output: the intake table filled in. Rule: at least 2 of the 3 outcomes must have a result; if fewer, stop and return only the missing-field questions. If the outcomes pass but F2, F4 or F8 is missing, do not stop: write the output with the placeholder "TO-CONFIRM" in place of the missing value, set Intake status to "complete with placeholders: [field list]", and list one open question per placeholder.
2. Fact register. Output: one row per fact, IDs F1 to F9 kept from the intake. Each outcome row also states whether a number exists ("number: yes" or "number: no").
3. Keyword filter. Output: the keywords kept. A keyword is kept only if a fact row supports it. Keywords with no fact are dropped and listed under "Dropped keywords". Never add a keyword the user did not give.
4. Headline options. Output: exactly 3 headlines, each on one line.
5. About draft. Output: 5 paragraphs in the fixed order below, 120 to 200 words in total (working value).
6. Trace table. Output: one row for every number, employer, title, date and tool name in steps 4 and 5.
7. Guard pass. Output: a final line stating the count of rows with status "no" (must be 0 before delivery, except TO-CONFIRM fragments when Intake status is "complete with placeholders").

## Formulas

Headline formulas (fill each slot from the register; keep each headline under the length the user's platform allows):

| Option | Formula |
|---|---|
| H1 | Role title, pipe, top two tools or methods, pipe, strongest outcome with its number |
| H2 | Role title, then "for" and the audience, then the verb of the strongest outcome |
| H3 | Role title, "with" and one tool, then one number from an outcome |

Platform limits: tell the user to check the current headline character limit on their platform. This skill does not state a limit as fact. Working value for drafting: 120 characters per headline.

About paragraph order:

| Para | Content | Length (working value) |
|---|---|---|
| P1 | Role, employer, scope from F3, audience from F8 | 2 sentences |
| P2 | Outcome 1: action, result, number | 2 sentences |
| P3 | Outcome 2: action, result, number | 2 sentences |
| P4 | Outcome 3: action, result, number | 2 sentences |
| P5 | One keyword cluster from the register and one plain call to action | 1 sentence |

Keyword placement rule:

| Keywords kept | Where they go |
|---|---|
| 1 or 2 | Headline H1 only |
| 3 or 4 | Headline H1 and P1 |
| 5 or more | Headline H1, P1, and the outcome sentence that uses the matching tool |

Use at most 5 keywords in total. Do not repeat a keyword in more than 2 places.

## Output contract

Return exactly these Markdown headings, in this order:

1. "## Intake status": one line, one of "complete", "complete with placeholders: [field list]" or "stopped: missing [field list]". With placeholders, the About may fall below 120 words and a "TO-CONFIRM" fragment may carry Status "no" in the trace table; both are expected and are listed under Open questions.
2. "## Fact register": table with columns ID | Fact | Number (yes/no).
3. "## Keywords": two lines, "Kept:" and "Dropped:", each comma-separated.
4. "## Headline options": three numbered lines H1, H2, H3.
5. "## About draft": five paragraphs, P1 to P5, no bullets.
6. "## Trace table": columns Fragment | Type | Fact ID | Status. Type is one of number, employer, title, date, tool, other. Status is "match" or "no".
7. "## Open questions": up to 3 questions for the user, or "none".

When Intake status is "stopped", return only that status line and the missing-field questions.

## Refuse / stop when

- Fewer than 2 of the 3 outcomes have a stated result.
- The user asks for an achievement, number, employer, title, date or tool that is not in the intake.
- The user asks for a superlative such as "best" or "top" with no fact that backs it.
- The user asks to copy a job posting's text into the profile instead of using keywords.
- The user asks for a different person's profile, or a profile for someone who has not supplied the facts.
- A trace row has status "no" after the guard pass, other than a TO-CONFIRM fragment under a placeholder status. Remove that fragment, then rerun step 7. If the fragment is essential, ask the user instead of keeping it.

## Quality rules

- Write in plain first person or plain third person, one tone for the whole About section.
- Prefer a number from the register over an adjective. Replace "strong" or "proven" with the number, or remove the word.
- Do not mention contact details, a phone number or a website unless the user supplied them in F8.
- Keep each sentence under 25 words (working value).
