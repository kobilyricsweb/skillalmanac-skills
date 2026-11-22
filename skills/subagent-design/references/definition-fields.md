# Subagent definition files (Claude Code)

## File and location

A Markdown file with YAML frontmatter; the body is the agent's system prompt.

| Location | Scope |
|---|---|
| `.claude/agents/<name>.md` inside the project | this project, shared through version control |
| `~/.claude/agents/<name>.md` | every project of this user |
| a plugin's `agents/` folder | wherever the plugin is enabled |

When names collide, the project file wins over the user file. Subfolders are scanned; identity comes from `name`, not the file path.

## Frontmatter fields

Only `name` and `description` are required.

| Field | Meaning | Guidance |
|---|---|---|
| `name` | Identifier used to call the agent | Lowercase words joined by hyphens; describes the job (`migration-reviewer`) |
| `description` | When to delegate to this agent | The trigger. What it does, then "Use when ...". Add "Use proactively" for automatic delegation |
| `tools` | Tools the agent may use, as a comma-separated list | Omitted means it inherits the caller's tools, including file writes. List them |
| `disallowedTools` | Tools removed from the pool | Wins over `tools`; an alternative way to remove `Write` and `Edit` |
| `model` | `haiku`, `sonnet`, `opus`, a full model id, or `inherit` | Omitted means the main conversation's model. Small model for search and summarising |
| `permissionMode` | Permission behaviour while the agent runs | Leave unset unless the user asks; never set a bypass mode on their behalf |
| `maxTurns` | Upper bound on agent turns | Useful for open-ended searches |
| `skills` | Skills whose full text is loaded at start | Each one costs context on every run |
| `isolation` | `worktree` runs the agent in a temporary git worktree | For agents that change files in parallel |
| `background` | Run in the background by default | |
| `memory` | `user`, `project` or `local` persistent notes | Turns on file writing for the notes folder |
| `hooks`, `mcpServers` | Hooks and MCP servers scoped to this agent | |

Read-only tool sets: `Read, Grep, Glob` for locating and reviewing; add `Bash` only when the agent must run a command (a diff, a test run), and say in the body which commands.

## What the agent starts with

- Its system prompt is the Markdown body plus basic environment details.
- The caller's message for this run (the brief).
- The project's instruction files, unless switched off for that agent.
- Not included: the conversation so far, files the caller already read, skills the caller already loaded.

Only its final message returns to the caller. Intermediate tool output does not.

## Description length

Descriptions of all agents are loaded into every session. Keep each to a few sentences and put detail in the body.

## Other tools

Other coding tools define custom agents in their own files and formats. The decisions in the skill (what to delegate, the brief, the report format) carry over; the fields above do not. Look up the target tool's current documentation before writing its file.

## Sources

Sub-agents page of the Claude Code documentation (code.claude.com/docs/en/sub-agents), read 2026-11-20.
