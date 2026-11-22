You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

The hook in infra-tools/ is supposed to block git force-pushes and rm -rf, but yesterday the agent still ran a force-push while working inside packages/api. Find out why and fix it. Write reply.md in the working folder with the causes you found.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
