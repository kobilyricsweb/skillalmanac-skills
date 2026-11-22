You are a coding agent working for a developer. Your workspace is the folder <local-path> . Treat it as the entire workspace: do not read, list or write anything outside it. First check whether the workspace has agent skills installed under .claude/skills/ ; if one applies to the request, read its SKILL.md and follow it. Write in English. The developer's request:

Be terse from now on. Give me the steps to rotate the production Postgres password for our app with zero downtime. The app reads DATABASE_URL from env; 3 app servers behind a load balancer; one DB role today (app_user). Write your answer to reply.md in the working folder, exactly as you would say it to me.

("The working folder" means the workspace folder above.) When finished, hand back a one-line confirmation only.
