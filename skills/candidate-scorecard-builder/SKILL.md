---
name: candidate-scorecard-builder
description: Builds a weighted candidate scorecard from interview notes. Use when a recruiter or hiring manager has two or more candidates with written notes and needs them compared on the same criteria, with weights, a 1-4 anchored scale, evidence for every score, and explicit totals. Do not use for making the hiring decision, for criteria based on protected traits, or for candidates who have no notes.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Candidate Scorecard Builder

Use this procedure to turn written candidate notes into one scorecard. Every candidate is scored on the same 4-6 weighted criteria, and every score cites a note. The output supports a human hiring decision. It does not make the decision.

## Workflow

1. **Intake.** Confirm the required facts: role title, two or more candidates, and each candidate's notes. Assign short labels (Candidate A, B, C). Output: nothing written to the final output. Keep the role title, labels, and note count per label for the sections below. If a required fact is missing, stop and use the stop rule below.
2. **Set criteria and weights.** Use the criteria the user supplies. If none are supplied, propose 5 job-related criteria and ask the user to confirm. Output: a criteria table with weights that total 100.
3. **Write the 4-anchor for each criterion.** The 4-anchor describes what a top score looks like in observable terms (a project, a measured result, a tested skill). Output: one anchor sentence per criterion. A criterion without an anchor cannot be scored; ask for one.
4. **Score each candidate on each criterion.** Apply the scale table below. Output: one row per criterion-candidate pair with a score and an evidence quote or paraphrase taken from that candidate's notes. If a candidate's notes say nothing on the criterion, do not score it: write MISSING with 0.00 points.
5. **Compute points and totals.** Points = score x weight / 4, rounded half-up to two decimals. Total = sum of points for that candidate, two decimals, maximum 100.00. Output: the points column and the totals table.
6. **Rank and apply the tie rule.** Output: ranks and any tie note.
7. **Check and write the output.** Confirm the weights total 100, every score has evidence, and every total equals the sum of its points. Set the status value. Output: the contract below, nothing else.

## Decision and threshold tables

**Weight rules (working values, not a published standard)**

| Rule | Value |
|---|---|
| Number of criteria | 4 to 6 |
| Weights per criterion | integers from 10 to 40 |
| Sum of all weights | exactly 100 |
| Points per score | score x weight / 4 |

**Scale (applies to every criterion)**

| Score | Label | Use when the notes show |
|---|---|---|
| 1 | Contradicted | The notes contain evidence that contradicts the criterion. The evidence cell quotes or paraphrases that note. |
| 2 | Partial | Related or indirect evidence only, or a narrow part of the criterion. |
| 3 | Meets | Direct evidence of the criterion at the level the role needs. One instance is enough. |
| 4 | Exceeds | Direct evidence above the role level, with a described outcome or measured result, or two or more separate instances. |

A criterion with no matching evidence in the notes is not scored 1. Its score cell reads MISSING, its points cell reads 0.00, and its evidence cell reads exactly: No matching evidence in notes.

**Tie rule**

| Step | Rule |
|---|---|
| 1 | Equal totals (to two decimals): the candidate with more points on the highest-weight criterion ranks higher. |
| 2 | Still equal: both candidates share a rank and the note reads "Tied; human review". |

**Status values**

| Status | Meaning |
|---|---|
| complete | Every score has evidence and every total is final. |
| partial | At least one criterion has no matching evidence in the notes. That cell shows MISSING with 0.00 points, and each affected total is labeled provisional. |
| blocked | A required intake fact is missing. No scores are given. |

## Output contract

Use exactly these headings, in this order:

```
# Candidate scorecard: <role title>

Status: complete | partial | blocked

## Criteria
| # | Criterion | Weight | 4-anchor |
(one row per criterion, then a row "Total weight | 100")

## Scores
| Criterion | Candidate | Score (1-4) | Points (of weight/4 max) | Evidence |
(one row per criterion and candidate, sorted by criterion then candidate label)

## Totals
| Rank | Candidate | Total (of 100.00) | Note |

## Tie note
(the tie note, or "None")

## Decision note
This scorecard supports a human hiring decision. It does not make the decision.
```

## Refuse or stop when

- **Protected traits.** Refuse any criterion based on age, sex, gender, race, ethnicity, national origin, religion, disability, pregnancy, marital or family status, sexual orientation, or any other trait protected in the user's jurisdiction. Refuse proxies too: graduation year as an age stand-in, first name, photo, home address or neighborhood, and accent. Name the criterion removed and propose a job-related replacement.
- **Fewer than two candidates**, or a candidate with no notes. Status blocked.
- **Missing intake facts.** Stop with status blocked and hand back this numbered list, asking only for what is missing:
  1. What is the role title?
  2. What are the notes for each candidate (paste text or a summary per candidate)?
  3. Which 4-6 criteria should be used, and what do top scores look like? Or should the skill propose them?
- **Invented evidence.** Do not score a candidate on a fact the notes do not state.
- **Requests for the decision.** Do not choose the hire, rank for rejection letters, or recommend an offer.

## Files

- `SKILL.md`: this procedure.
- `LICENSE.txt`: Apache License 2.0.
