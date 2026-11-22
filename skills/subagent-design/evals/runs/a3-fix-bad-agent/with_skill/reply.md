# What was wrong with the helper subagent

The README says helper exists so the main session can ask "where is X defined / where is X used" without filling its context with search output. The old definition did not say that anywhere.

- **Never picked:** the description was "Helps with code." It has no trigger, so the main agent could not tell when to delegate. The new description says what it does and "Use proactively when ... where is X defined / used".
- **Wall of text:** the body said "Explain everything you looked at in detail" and had no report format. It now has a fixed report: verdict, locations with quoted lines, not-checked, assumptions, at most 30 lines, no search narrative.
- **Edits files:** there was no `tools` field, so it inherited every tool including Write and Edit, and the body said "Feel free to fix small issues". It now has `tools: Read, Grep, Glob` and the body says not to modify files.
- **Also fixed:** the body said "Continue from what we discussed above", but a subagent cannot see the conversation. It now says how to find its input (the caller's message names the symbol). It also said to ask the user, which a subagent cannot do; it now states assumptions in the report. The model was `opus` for a search job; it is now `haiku`.
- **Name:** `Helper Agent` is now `code-locator` (lowercase, hyphenated, describes the job). The file is `webapp/.claude/agents/code-locator.md`, and the old `helper.md` is removed so there is no duplicate.

Check: the definition passed the lint script. Not tested in a live session. Try two or three real "where is X used" requests, such as `formatPrice`. Whether it is picked automatically also depends on the harness and the other installed agents. If other docs or scripts call it `helper`, update them.
