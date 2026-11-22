# LinkedIn export to resume

## One line

Drafts a reverse-chronological resume from pasted profile export text, with a fact ledger for every line and a GAPS list for what the export does not say.

## What it does

The skill takes the text of a profile export that someone has pasted into the chat. It reads the name, headline, about text, positions, education and skills, then writes a resume in a fixed section order: summary, experience, education and skills. Positions are sorted newest first by start month and year. Each description is split into sentences, and each sentence becomes one bullet, copied word for word. The skill does not reword bullets, merge them or add words to them.

Every resume line gets an ID in a fact ledger that shows the exact text used. A second table, GAPS, lists what the export leaves out: a missing start date, a missing end date, a position with no description, a position whose bullets carry no number, an education entry with no years, or an empty skills block. Each gap comes with a question the user can answer by pasting more text.

The skill sets one of three statuses. Complete means no gaps. Partial means gaps or refused requests. Blocked means a required fact is missing, and then no draft is written at all.

## When to use

Use it when someone has the text of their own profile export and wants a resume draft that stays faithful to what the profile says. It suits people who keep their career history in a profile and want a first draft to edit, and it suits anyone reviewing a draft for missing facts before sending it out.

## When not to use

Do not use it to fetch a live profile or a web address, to write a cover letter, or to edit a resume that already exists as a file. It will not invent titles, achievements, dates or numbers that the export lacks. A request for those is refused, and the rest of the draft still comes back.

## Requirements

A text-capable agent. The skill needs no network access, no scripts and no installed packages. The input is the pasted export text, with a name and at least one position that has a title and a company.

## Example

Input, abridged to the lines the skill used:

```
Name: Jordan Example
Headline: Operations Analyst at Bluefield Analytics
About: Analyst who builds reporting for warehouse teams.
Position 1: Operations Analyst | Bluefield Analytics | Mar 2022 - Present | Denver, CO
  Description: Built weekly inbound reporting for three warehouses. Cut manual data prep by 40 percent. Trained 6 coworkers on the reporting tool.
Position 2: Data Coordinator | Oakline Logistics | Jun 2019 - Feb 2022 | Aurora, CO
  Description: Maintained shipment records in the warehouse system. Reconciled carrier invoices each month.
Position 3: Intern | Oakline Logistics | May 2018 - Aug 2018
  Description:
Education: State University | BS, Supply Chain Management | 2015 - 2019
Skills: SQL, Excel, Tableau
```

Output:

```
## Status
Status: partial. Positions: 3. Bullets: 5. Ledger rows: 13. Gaps: 2.

## Resume draft
# Jordan Example
Operations Analyst at Bluefield Analytics

### Summary
Analyst who builds reporting for warehouse teams. [F03]

### Experience
**Operations Analyst | Bluefield Analytics | Mar 2022 - Present | Denver, CO** [F04]
- Built weekly inbound reporting for three warehouses. [F05]
- Cut manual data prep by 40 percent. [F06]
- Trained 6 coworkers on the reporting tool. [F07]

**Data Coordinator | Oakline Logistics | Jun 2019 - Feb 2022 | Aurora, CO** [F08]
- Maintained shipment records in the warehouse system. [F09]
- Reconciled carrier invoices each month. [F10]

**Intern | Oakline Logistics | May 2018 - Aug 2018** [F11]
No bullets: the export has no description. [G02]

### Education
**State University | BS, Supply Chain Management | 2015 - 2019** [F12]

### Skills
SQL, Excel, Tableau [F13]

## Fact ledger
| ID | Section | Export label | Text used (verbatim) |
|---|---|---|---|
| F01 | Header | Name | Jordan Example |
| F02 | Header | Headline | Operations Analyst at Bluefield Analytics |
| F03 | Summary | About | Analyst who builds reporting for warehouse teams. |
| F04 | Experience 1 | Position 1 heading | Operations Analyst \| Bluefield Analytics \| Mar 2022 - Present \| Denver, CO |
| F05 | Experience 1 | Description sentence 1 | Built weekly inbound reporting for three warehouses. |
| F06 | Experience 1 | Description sentence 2 | Cut manual data prep by 40 percent. |
| F07 | Experience 1 | Description sentence 3 | Trained 6 coworkers on the reporting tool. |
| F08 | Experience 2 | Position 2 heading | Data Coordinator \| Oakline Logistics \| Jun 2019 - Feb 2022 \| Aurora, CO |
| F09 | Experience 2 | Description sentence 1 | Maintained shipment records in the warehouse system. |
| F10 | Experience 2 | Description sentence 2 | Reconciled carrier invoices each month. |
| F11 | Experience 3 | Position 3 heading | Intern \| Oakline Logistics \| May 2018 - Aug 2018 |
| F12 | Education | Education entry | State University \| BS, Supply Chain Management \| 2015 - 2019 |
| F13 | Skills | Skills line | SQL, Excel, Tableau |

## Gaps
| ID | Code | Location | Question to the user |
|---|---|---|---|
| G01 | NO_METRIC | Position 2, Data Coordinator | Did this role have a number you can cite, such as a count, a percent or time saved? Paste it if so. |
| G02 | NO_DESCRIPTION | Position 3, Intern | What duties did this internship include? Paste them as sentences. |

## Open questions
None.
```

## Limits

The skill checks only the text it is given. It cannot confirm that the export is current, that the person still holds the roles, or that the dates are right. It does not judge whether a bullet is a strong achievement, and it does not rank skills by relevance to a job. Sentence splitting is a plain split at periods, so an abbreviation such as a job title with a period may split in the wrong place. Layout, fonts and page length are outside its scope. The draft reflects what the export says, so any claim about the person is only as reliable as the export itself.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
