You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

Review the change in notifier/ before I merge it. The diff is notifier/change.diff, the description is notifier/PR.md, and the repo is checked out with the change applied. Write the review to reply.md in the working folder.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
