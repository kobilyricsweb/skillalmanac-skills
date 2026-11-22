---
name: blameless-postmortem-writer
description: Writes a blameless incident postmortem from raw responder notes and a UTC timeline, using fixed headings, contributing factors described by system and process, and action items that each carry an owner, a due date and a checkable done-condition. Use when an incident is resolved and the team needs a postmortem from notes, chat logs or a rough timeline, or when a draft names people as causes and must be rewritten. Do not use for live incident triage or status updates during an outage, for security breach forensics, for legal or regulatory filings, or for code review without an incident.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Blameless postmortem writer

Produce one postmortem document for one resolved incident. The input is the user's notes. The output is a single Markdown document with the headings listed in the output contract. Do not add sections, rename headings or reorder them.

## Step 1. Intake check

Output: a list named "Missing inputs" (goes into Author notes at the end).

Check for these fields, in this order:

1. Incident title and calendar date.
2. Start time of customer-facing impact (UTC).
3. Detection time and detection method (alert name, customer report, or staff observation).
4. Mitigation time (when the harm stopped growing) and resolution time (when the team declared it over).
5. Impact figures supplied by the user (duration, failed requests, affected customers, or other counts).
6. Severity criteria supplied by the user.
7. Contributing details: what changed, what the system did, what the responders did.

Mark any absent field as "not provided". Never estimate a missing value.

## Step 2. Normalise timestamps

Output: every timeline entry in UTC as HH:MM, with a date once per document.

- If a note gives a local time and an offset is stated, convert it. If no offset is stated, stop and ask for it (see Refuse / stop when).
- Drop entries with no time. Keep them in Author notes as "untimed notes".
- Any silence of more than 15 minutes between two consecutive timeline entries is written as a row "gap, no entries" in the timeline. This 15-minute value is a working value.

## Step 3. Compute the metadata durations

Output: four integers in minutes, computed only from the timestamps in Step 2.

| Metric | Formula | If an input is missing |
|---|---|---|
| Duration | resolved minus impact start | "not provided" |
| Time to detect | detected minus impact start | "not provided" |
| Time to mitigate | mitigated minus detected | "not provided" |
| Time to resolve after mitigation | resolved minus mitigated | "not provided" |

If a computed value is negative, stop and report the conflicting timestamps in Author notes. Do not reorder them.

## Step 4. Severity

Output: one severity label and the criterion that matched.

| Situation | Label written in the document |
|---|---|
| User supplied criteria and exactly one matches | the label from the user's scale |
| User supplied criteria and none matches | "unclassified" plus the nearest criterion in Author notes |
| User supplied criteria and two match | the higher label, with both criteria cited |
| No criteria supplied | "not provided, criteria needed" |

Never choose a severity from your own judgement of the impact.

## Step 5. Contributing factors

Output: 2 to 6 numbered factors. Each factor line has this form:

`N. [System|Process|Environment] <mechanism in one sentence>. Evidence: <quote or paraphrase of the note>.`

Rules:

- System covers code, configuration, infrastructure and dependencies.
- Process covers change review, rollout method, runbooks, alert design and on-call handoffs.
- Environment covers load, traffic patterns and third-party providers.
- Describe what the system or process allowed to happen. Never write a person's name, role-as-blame or pronoun as the cause.
- Fewer than 2 factors: stop and ask for more notes. More than 6: merge the closest two until 6 remain.

## Step 6. What went well

Output: 2 to 4 bullets. Each bullet points to one timeline row, for example "Alert fired inside the 5-minute target (14:09)". If the notes record nothing positive, write "None recorded in notes." Do not invent praise.

## Step 7. Action items

Output: a table with the columns in the output contract. Each action needs all five fields.

Action types and due-date windows (working values, counted from the resolution date):

| Type | Purpose | Due within (days) |
|---|---|---|
| Mitigate | faster rollback or safeguard | 14 |
| Detect | alert, dashboard or check | 30 |
| Prevent | code, config or pipeline guard | 45 |
| Process | runbook, review checklist or training material | 60 |

Rules for done-conditions:

- The done-condition names an observable artifact: a test that fails on the bad value, an alert visible in a named tool, a runbook section that exists, a checklist field that is required.
- Words such as "improve", "consider", "review", "better" or "ensure" alone are not done-conditions. Rewrite them into a check.
- Owner is a team or role (for example "payments on-call lead"). If the user names a person as owner, keep the name only in the owner field.
- At least one Detect item when detection took longer than 10 minutes (working value) and at least one Prevent or Process item for each contributing factor of type System or Process.

## Step 8. Blame check

Scan the draft before output. Rewrite any sentence that:

- names a person as the actor of a failure,
- uses "should have", "failed to" or "forgot" with a person as subject,
- implies carelessness as a cause.

Rewrite each to the system or process form, for example "The rollback required editing the config file by hand, and the runbook did not list the file path." Count the rewrites and record the count in Author notes.

## Step 9. Assemble the output

Write the document in the exact contract below. Use "not provided" for every missing value.

## Output contract

Headings, in this order, exactly as written:

1. `# Postmortem: <incident title>`
2. `## Summary` - 3 to 5 sentences. No person names.
3. `## Metadata` - table with columns `Field | Value`. Rows, in this order: Incident date, Impact start (UTC), Detected (UTC), Mitigated (UTC), Resolved (UTC), Duration (min), Time to detect (min), Time to mitigate (min), Time to resolve after mitigation (min), Severity, Detection method.
4. `## Impact` - bullets. Each bullet is one user-supplied figure with its source note in brackets. Missing figures are a bullet reading "not provided".
5. `## Timeline` - table with columns `Time (UTC) | Event | Source note`.
6. `## Contributing factors` - the numbered list from Step 5.
7. `## What went well` - bullets from Step 6.
8. `## Action items` - table with columns `ID | Action | Type | Owner | Due (YYYY-MM-DD) | Done when`. IDs are AI-1, AI-2 and so on.
9. `## Author notes` - bullets: Missing inputs, untimed notes, blame rewrites (count), assumptions made by the author (must be none unless the user agreed).

## Refuse / stop when

- The user asks for a person to be named as the cause or blamed. Rewrite to the mechanism. If the user insists on the name, refuse and say why in Author notes.
- The user asks for timestamps, durations, impact counts or a severity that are not in the notes. Write "not provided" and say so.
- Start time or resolution time is missing. Stop and ask for it.
- Times have no offset and cannot be placed in UTC. Stop and ask for the offset.
- Fewer than 2 contributing factors can be supported by the notes. Stop and ask for more notes.
- The incident is an active outage. Redirect to live incident triage; this skill writes after resolution.
- The incident is a security breach, a legal matter or a regulatory filing. Out of scope.
- An action item's done-condition cannot be made checkable after one rewrite. Drop it and list it in Author notes as "not written, no checkable condition".
