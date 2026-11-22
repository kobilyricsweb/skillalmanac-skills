---
name: subagent-design
description: Designs subagents and delegation briefs for coding agents, deciding what to delegate and writing definition files with a trigger description, least-privilege tools and a fixed report format. Use when the user asks for a subagent, custom agent, agent team, parallel agents, or a prompt or brief to hand to another agent, asks whether something should be a subagent or a skill, or has an agent that is never picked, returns walls of text or changes files it should not. Do not use for building multi-agent applications with an SDK or framework, or for writing skills or hooks.
license: Apache-2.0
compatibility: The delegation and brief rules are tool-neutral. The definition file format and the lint script target Claude Code subagent files (Markdown with frontmatter in .claude/agents); other tools use different files. The lint script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Subagent design

A subagent starts with nothing from the conversation that spawned it and hands back one message. Everything it needs has to be in its definition or its brief; everything the caller needs has to be in that one message. Most failed delegations are a failure of one of those two handoffs.

## 1. Decide what to delegate

Go through the work item by item and state the decision for each, with the reason.

| Delegate when | Keep in the main conversation when |
|---|---|
| The work produces a lot of output the caller does not need to keep (searches, logs, test runs) | The work needs the conversation so far, or back-and-forth with the user |
| Pieces are independent and can run at the same time | The piece is the synthesis: the plan, the decision, the final answer |
| The work needs different permissions (read-only review, isolated worktree) | It is a handful of tool calls or a lookup whose target is known |
| A second opinion is wanted that is not anchored on the caller's view | The result must be checked line by line anyway |

Rules that follow:

- **Do not delegate the conclusion.** Agents gather; the caller decides. A plan written by an agent that has not seen the conversation is a plan for a different problem.
- **Independent pieces go out together**; dependent pieces go in order, and the later brief is written after the earlier result is in.
- Subagent or skill: a skill adds instructions to the current context; a subagent moves work out of it. Reusable procedure that needs the conversation is a skill. Bulky or restricted work is a subagent.

## 2. Write a reusable definition

For the file format, the fields and where the file goes, read [references/definition-fields.md](references/definition-fields.md). Start from [assets/agent-template.md](assets/agent-template.md). Place the file in the agents folder of the project the user named; if the workspace holds the project in a subfolder, the file goes inside that project, not at the workspace root.

**Description** is the only thing the main agent reads when choosing. Write it as: what the agent does, then `Use when <concrete triggers>`, including the file types, paths or phrases that should cause delegation. Add "Use proactively" when the user wants it picked without being asked. "Helps with code" is never picked.

**Tools**: list them. A reviewer, researcher or locator gets read and search tools only. An omitted tools field inherits everything, including file writes. Give shell access only when the job needs to run something, and say in the body what it may run.

**Model**: choose by the job. Search and summarising jobs run well on a small, fast model; judgement-heavy review should inherit or use a strong one. Say which and why.

**Body**, in this order:

1. Role in one sentence, and what it must not do (for a reviewer: "Do not modify files").
2. **How to find its input.** It cannot see the conversation. Tell it how to locate the work: the diff command, the folder, the file pattern, or "the caller's message names the target".
3. **Project facts it must apply**, copied in from the repo's own docs with the reason for each. An agent told "follow our migration rules" applies none; an agent given the five rules applies five. Read the contributing guide, instruction files and incident notes and carry the specifics over.
4. Procedure, as numbered steps, when order matters.
5. **Report format** (section 4).
6. What to do when stuck: it cannot ask the user. It states the assumption it made, or returns the open question as part of the report.

Then run the check:

```bash
python scripts/agent_def_lint.py path/to/agent.md
```

Run the script; do not edit it to pass. Fix each `ERROR`; fix or justify each `WARN`. Without Python, check the same points by hand: description has a trigger and is over 80 characters, tools listed and matching the role, no reference to earlier conversation, no instruction to ask the user, a report format, a length bound.

## 3. Write a one-off brief

For a single delegation, fill [assets/brief-template.md](assets/brief-template.md). Every brief has:

- **Goal** and why it is wanted, in two sentences. The why lets the agent make sensible calls at the edges.
- **Scope**: the paths to look in and the paths to leave alone.
- **What is already known or ruled out**, so it is not rediscovered. Mark it as a hint to verify, not as the answer: an agent handed a conclusion tends to return it confirmed.
- **Traps**: the cases a naive pass misses. For a search: indirect references (keys built from strings, config and deploy files, tests, docs, generated code), not only the literal text.
- **Constraints**: read-only or not, what it may run, what it must not touch.
- **Done when**: the stopping condition.
- **Return format** (section 4).

Test for self-containment: could a contractor who has never seen this conversation act on the brief alone? Phrases such as "as discussed", "the bug above", "continue" fail the test.

## 4. Fix the report format

The report is written for the caller's next step, so design it backwards from that step.

- First line: the verdict or answer (`PASS`, `BLOCK`, `FOUND 4`, `NOT FOUND`).
- Then findings as a list or table with **evidence the caller can check without redoing the work**: file path, line number, the quoted line or command output.
- Separate what was verified from what was inferred.
- List what was not checked.
- A length bound in numbers ("at most 30 lines", "no narrative of the search").

## 5. Say how results will be checked

Returned work is a claim. Before relying on it, the caller spot-checks: open two or three of the cited locations, rerun one command, and treat "found nothing" as unproven until one independent search agrees. State this check in the answer to the user, and state the cost: each agent spends tokens of its own, so say how many agents the plan uses.

## Fixing an agent that misbehaves

| Symptom | Usual cause | Fix |
|---|---|---|
| Never picked automatically | Description is vague or has no trigger | Rewrite as what plus "Use when ..." with real trigger words |
| Returns a wall of text | No report format, or it was told to explain everything | Fixed format, evidence fields, numeric length bound |
| Edits files it should not | No tools list (inherits all), or the body invites fixes | List read-only tools; state "do not modify files" |
| Answers a different question | Body assumes the earlier conversation | Tell it how to find its input; make the brief carry the question |
| Stalls or guesses silently | Told to ask the user, which it cannot | Have it state assumptions and return open questions |
| Slow or costly for a simple job | Model too large for the work | Smaller model or inherit |

Give the user the cause of each symptom they reported, not only the new file.

## Limits

- Whether an agent is picked automatically also depends on the other agents installed and on the harness; a good description raises the odds and guarantees nothing. Tell the user to try two or three real requests.
- The lint script checks form (fields, wording patterns, length), not whether the agent does good work.
- Field names and locations in the reference describe one tool. For another tool, keep sections 1, 3, 4 and 5 and look up that tool's file format.
