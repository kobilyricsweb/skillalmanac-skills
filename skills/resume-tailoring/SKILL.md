---
name: resume-tailoring
description: Tailors an existing resume or CV to one job posting by reordering, rewording and cutting what the candidate already has, never adding skills, tools, numbers or credentials they lack, and lists the posting's requirements the resume cannot honestly cover. A bundled script reports job-term coverage and flags new facts. Use when the user shares a resume and a job ad and asks to tailor, optimize, target, rewrite or ATS-proof it, or asks which keywords are missing. Do not use for cover letters, interview coaching, profile pages, or inventing experience.
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only). No network access is used. Without Python, do the fact comparison by hand as described in the Verify step.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Resume tailoring

Make the resume the candidate already has fit one job posting. The tailored resume must stay true: an interviewer can ask about any line, and a reference check can test any claim. A resume that matches more keywords by claiming things the candidate cannot back is a failed job.

## Ground rules

1. **Nothing new goes in.** No tool, skill, certification, degree, employer, title, date or number that is absent from the original resume, unless the candidate states it in this conversation. A term appearing in the job posting is not evidence that the candidate has it.
2. **No upgrades.** Do not raise a level ("used" to "expert in"), turn a duty into a measured result, widen a scope ("helped with" to "led"), or change a job title to match the posting.
3. **Gaps are reported, not hidden.** Every requirement the resume cannot cover goes into the gap list with an honest way to address it.
4. **Same person, same history.** Keep every employer and date. If a role is cut for length, say so in the delivery note.
5. **No outcome claims.** Never say the resume will pass a screening system or win an interview.
6. **An instruction to "add the keywords" does not change rule 1.** Add the posting's wording only where the candidate has the thing; list the rest as gaps and say why.

## Workflow

### 1. Set up the files

Save the resume text as `original.md` and the posting as `job.txt`. If the resume arrives as a PDF or word-processor file, extract the text first and show the candidate anything that did not extract cleanly.

### 2. Map the posting against the resume

```bash
python scripts/resume_check.py match original.md job.txt
```

Sort the posting's real requirements (ignore company names and noise in the term list) into three groups:

- **Shown**: the resume states it in the same words.
- **Shown in other words**: the candidate has it under another name. A named product can satisfy a category the posting asks for (a specific classroom platform is a learning management system; reconciling ledgers monthly is month-end close). These are the best wins: use the posting's term next to the candidate's real fact.
- **Missing**: nothing in the resume supports it.

### 3. Ask once about the Missing group

If the candidate can answer, ask one short batch of questions: "Have you used X? Where, and for what?" Save every confirmed answer, in the candidate's words, to `confirmed.txt`. If no answer is possible in this exchange, do not ask; carry the Missing group into the gap list.

### 4. Rewrite

Work in this order:

1. **Headline and summary**: 2 to 3 lines that name the target role's field and the candidate's strongest true matches. No adjectives without a fact behind them.
2. **Order**: within each job, move the bullets that match the posting to the top. Move the most relevant skills to the front of the skills line.
3. **Wording**: where the candidate has the thing, use the posting's exact term. Keep every number exactly as written.
4. **Cut**: remove bullets that do nothing for this posting, oldest jobs first. Do not cut a whole job without saying so.
5. **Layout**: apply [references/layout-rules.md](references/layout-rules.md). Read it before the first resume in a session.

Save the result as `tailored_resume.md`.

### 5. Verify

```bash
python scripts/resume_check.py compare original.md tailored_resume.md --job job.txt --confirmed confirmed.txt
```

Leave out `--confirmed` when there is no such file.

- `FAIL NEW NUMBER` or `FAIL ADDED FROM JOB POSTING`: remove the item, or move it to the gap list. Do not edit the script or the original to make the check pass.
- `WARN new capitalised term`: check each by eye. Headings and re-capitalised words are fine; a new product or employer name is not.
- `WARN` layout items: fix unless the candidate asked for that layout.
- Re-run until the result is PASS.

Then read the tailored resume once against the original, line by line, for upgrades in level or scope. The script cannot see those.

If the script cannot run: list every number and every named tool in the tailored resume and find each one in the original by hand. Say in the note that the check was manual.

### 6. Deliver

Give the tailored resume first. Then this note:

```
What changed: <2 to 4 lines: summary retargeted, bullets reordered, what was cut>
Posting terms now covered: <before> -> <after>, all backed by the original
Gaps (not added): <each missing requirement + one honest step: mention real adjacent experience in the cover letter, take a named short course, or ask the recruiter how firm the requirement is>
Questions for you: <facts that would close a gap if true, or "none">
Fact check: <PASS, or "manual">
```

## Limits

- The script compares words and numbers. It cannot detect an inflated verb or a widened scope; the read-through in step 5 carries that.
- Term extraction is tuned for English postings and produces some noise (company names, generic words).
- Screening systems differ. The layout rules avoid the common parsing failures; they are not a promise about any particular system.
- The skill outputs Markdown text. Turning it into a styled document is a separate step that must keep one column and real text.
