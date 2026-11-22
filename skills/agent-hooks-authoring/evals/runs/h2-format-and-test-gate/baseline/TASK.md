You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

Set up two hooks for this repo (shop-api/): (1) after the coding agent edits a .js or .ts file, run our formatter on just that file (npm run format -- <file>); (2) don't let the agent end its turn while npm test is failing, it should keep working until the tests pass. The team is on macOS, Linux and Windows (Git Bash). Write a short reply.md in the working folder saying what you did.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
