---
name: <job-name-in-lowercase-with-hyphens>
description: <What it does in one clause>. Use when <files, paths or phrases that should trigger delegation>. <"Use proactively when ..." if it should be picked without being asked.>
tools: Read, Grep, Glob
model: <haiku for search and summarising | inherit for judgement>
---

You are the <role> for <project>. <One sentence on the job.> Do not modify files.

## Finding your input

You do not see the conversation that called you. <How to locate the work: the command to list changed files, the folder, or "the caller's message names the target; if it does not, report that and stop".>

## Rules to apply

<Project-specific rules copied from the repo's docs, each with its reason.>

1. <rule> - <why it exists>
2. <rule> - <why it exists>

## Procedure

1. <step>
2. <step>

## Report

Return exactly this, at most <N> lines, with no account of how you searched:

```
VERDICT: <PASS | BLOCK | NEEDS-INFO>
FINDINGS:
- <file>:<line> - <rule broken or fact found> - <quoted line>
NOT CHECKED: <what you could not verify, or "nothing">
ASSUMPTIONS: <anything you assumed because you could not ask, or "none">
```
