You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

Create a subagent for this project (ledger-service/) that reviews database migration files before they get merged. I want it to be picked up automatically whenever migrations are touched. Write a short reply.md in the working folder saying what you created and why.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
