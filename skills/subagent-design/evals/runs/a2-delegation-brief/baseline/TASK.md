You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

In storefront/ I need three things: find every place that reads the LEGACY_BILLING flag, separately check which npm dependencies are unused, and then write the plan for removing the flag. Use subagents where it makes sense. Don't run them: I want to see the exact prompts you would send first. Write your answer to reply.md in the working folder.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
