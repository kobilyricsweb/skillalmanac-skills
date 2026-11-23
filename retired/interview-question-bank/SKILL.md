---
name: interview-question-bank
description: Builds one fixed interview question set for one role, with four or five competencies taken from the role's outcomes, two past-behavior questions per competency, one follow-up probe per question, and four-point scoring anchors. Use when a hiring manager or panel needs identical questions for every candidate, when interviews drift into small talk, or when scoring anchors are needed before the first interview. Do not use for writing job descriptions, screening resumes, ranking candidates, or scoring a finished interview.
license: Apache-2.0
compatibility: None beyond a text-capable agent; no scripts and no network access.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Interview question bank

Builds one question set for one role, tied to that role's outcomes. The same set, in the same order, goes to every candidate.

## Required intake

| Code | Fact | Pass test |
|------|------|-----------|
| R1 | Role title | One line of text |
| R2 | Outcomes the hire must deliver in the first 12 months | Three or more outcomes, one sentence each |
| R3 | Level | One of: individual contributor, lead, manager |

No other facts are used. Do not infer a role title, outcome, or level the user did not write.

## Workflow

1. Check intake. Test R1 to R3 against the table above. Output: the Intake check table (Fact | Value). If any test fails, follow the Stop rule below.

2. Set the counts. Count the R2 outcomes and use this table. The counts apply everywhere in the output.

| R2 outcomes | Competencies | Questions (two each) | Maximum score |
|-------------|--------------|----------------------|---------------|
| 3 or 4 | 4 | 8 | 32 |
| 5 or more | 5 | 10 | 40 |

   Working values, not a published standard: the word limits (30, 15, 12), the three-item lists, and the five-question partial cap.

   Each competency is a noun phrase naming one observable skill, such as "Handling escalations". Each competency maps to at least one outcome. Drop any trait that cannot appear in a past example, such as "passion", "culture fit", or "energy". Output: the Competencies table, IDs C1 to C4 or C5.

3. Write two questions per competency. Each question starts with "Describe" or "Tell me about a time" and asks for a real past event. No hypotheticals ("What would you do if"). Maximum 30 words. IDs run C1-Q1, C1-Q2, C2-Q1, and so on. Wording is fixed: no candidate-specific phrasing. Scope follows R3: for individual contributor, ask only about the candidate's own work; for lead or manager, a question may ask about a team the candidate led.

4. Write one follow-up probe per question. The probe asks for one detail not yet given: the candidate's own action, the result, or the next step. Maximum 15 words. One probe per question, no more.

5. Write the answer guide. For each question, write exactly three "Strong answer contains" items and exactly three "Weak answer contains" items. Each item is at most 12 words and describes content (actions, numbers, results), never personality.

6. Write four scoring anchors per question, for scores 1 to 4, each at most 15 words. Use this default ladder, then rewrite each rung in the question's own terms (nouns from the question):
   - 1: no past example, or no action by the candidate.
   - 2: the candidate acted but gives no result.
   - 3: the candidate acted and reports a result against a stated target.
   - 4: as 3, plus a lasting change the candidate made afterward.

7. Screen for protected topics. Check every question, probe, and answer item against the table below. Replace a flagged question with a rewritten question on the same competency that passes the screen, and record the removal. Never drop a question without a replacement, because the counts in step 2 must hold.

| Topic | Remove wording such as |
|-------|------------------------|
| Age or date of birth | years until retirement, graduation year, age |
| Family or marital status | children, pregnancy, childcare, spouse, plans for a family |
| Health or disability | medical conditions, medication, disability, sick-leave history |
| Religion or observance | church, prayer, religious holidays, faith-based diet rules |
| National origin, race, ethnicity, citizenship, accent | where you were born, family origin, accent |
| Sexual orientation or gender identity | sexual orientation, partner's gender, gender identity |
| Political or union affiliation | party membership, voting, union membership |

8. Assemble the bank using the output contract below. The Removed items table appears even when empty, with a single row reading None.

## Stop rule (intake incomplete)

If any R1 to R3 test fails, or an R2 outcome is not one sentence, write no questions. Return the partial output below, with a numbered list of up to five questions, one per failed fact, asking the user for the missing text. Stop after the list. Do not guess a missing role title, outcome, or level.

## Refuse / stop when

- Any R1 to R3 test fails (partial output, above).
- The request asks for a question on a topic in the screen table, including "for the record" or "legal will not mind". Remove it, and name the removed item and topic in the report.
- The request asks to screen out, filter, or rank candidates by a topic in the screen table. Refuse and say why.
- The request asks this skill to score or rank a named candidate's real answers. This skill writes the bank only.
- The request asks for more than five competencies or more than two questions per competency. Decline and use the counts in step 2.

## Output contract

Complete output, headings in this order:

1. `# Interview question bank: <role title>`
2. `## Status`, then one line: `Status: complete`
3. `## Intake check`, table `| Fact | Value |`, rows R1, R2, R3
4. `## Competencies`, table `| # | Competency | Outcome it maps to |`, one row per competency
5. `## Questions`, one block per question in ID order. Lines in this order: `**C1-Q1** <question>`, `Probe: <probe>`, `Strong answer contains:` with three bullets, `Weak answer contains:` with three bullets, then `Score 1:`, `Score 2:`, `Score 3:`, `Score 4:` lines
6. `## Removed items`, table `| Removed item | Topic | Replacement |`. Replacement is the ID of the question that took its place, or None.
7. `## Scoring`, one line: each question scores 1 to 4, each competency maximum is 8, the bank maximum is 32 (four competencies) or 40 (five competencies)

Partial output, only these sections: `# Interview question bank: <role title or unnamed role>`, `## Status` with `Status: partial`, and `## Questions needed` as a numbered list.

## Files

- `SKILL.md`: this procedure.
- `LICENSE.txt`: Apache License 2.0 text.
