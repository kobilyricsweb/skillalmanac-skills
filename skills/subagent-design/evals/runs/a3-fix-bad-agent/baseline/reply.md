# What was wrong with webapp/.claude/agents/helper.md

1. Never auto-selected: the description was "Helps with code." which is too vague to match any request. The description is what the main session uses to decide delegation. It now states the purpose (locate where symbols are defined or used) and says "use proactively".
2. Name: "Helper Agent" is not a valid identifier (should be lowercase with hyphens) and did not match the file or the README's `helper`. Now `name: helper`.
3. Edited files: no `tools` field meant it inherited every tool, and the prompt said "Feel free to fix small issues". Now `tools: Read, Grep, Glob` and the prompt says never to modify files.
4. Wall of text: the prompt said "Explain everything you looked at in detail". Replaced with a concise output format capped at 15 lines (definition, usages, notes).
5. Context assumptions: "Continue from what we discussed above" is meaningless because a subagent starts with a fresh context. Removed; it works from the task it is given. "Ask the user before continuing" was also removed since a subagent cannot reliably ask; it states its interpretation and answers.
6. Model: opus was overkill for grep-style lookups; switched to haiku (change back if you need deeper reasoning).
