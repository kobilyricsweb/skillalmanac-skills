You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

The subagent in webapp/.claude/agents/helper.md never gets picked automatically, and when I do call it, it comes back with a wall of text and sometimes edits files it shouldn't. Fix it. Write reply.md in the working folder with what was wrong.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
