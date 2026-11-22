# One source of truth for agent instructions

## What changed

- `mobile-backend/AGENTS.md` (new) is now the single place to edit shared instructions. Codex and Cursor read `AGENTS.md` natively, so neither needs a copy.
- `mobile-backend/CLAUDE.md` is now just `@AGENTS.md` (Claude Code's import syntax) plus the "Claude Code only" section. Claude Code does not read `AGENTS.md` by itself, so this one-line import is the bridge. There is no duplicated text and no symlink (symlinks are unreliable on Windows checkouts).
- `mobile-backend/.cursor/rules/general.mdc` is deleted. It was a hand-maintained copy of the same rules, and `AGENTS.md` is always applied in Cursor, so it was redundant. Add `.cursor/rules/*.mdc` files later only for Cursor-specific or path-scoped rules.
- `.claude/agents/db-reviewer.md` is untouched. It is a Claude Code subagent and has no equivalent in the other tools.

## Where things go now

| Content | File |
| --- | --- |
| Commands and rules for everyone | `AGENTS.md` |
| Claude-only items (the `db-reviewer` subagent, the gofmt hook note) | `CLAUDE.md`, below the import |
| Subagent definitions | `.claude/agents/` |

## Conflicts I found while merging, and how I resolved them

The two files had already drifted apart:

1. **Go version**: `CLAUDE.md` said Go 1.22 and the Cursor rule said Go 1.21. `go.mod` declares `go 1.22`, so I used **1.22**. Cursor and Codex users were previously being told to avoid 1.22 features, so tell them the rule is now 1.22.
2. **Logging rule**: "Never log request bodies" (PII, logs shipped to a third party) existed only in the Cursor rule. Claude Code users were never told. I added it to `AGENTS.md`, so it now applies to every tool. Please confirm it is a real, team-wide rule.
3. **Details only in CLAUDE.md** (the `fmt.Errorf("...: %w", err)` form, "no bare returns of driver errors", the openapi.yaml requirement, `int64` for money) were kept, since the Cursor version was just a shorter paraphrase.

## Left in CLAUDE.md on purpose

The "Claude Code only" section stays in `CLAUDE.md` because the other tools would read it as instructions for tools they do not have. The `db-reviewer` rule is meaningful only in Claude Code. The gofmt hook note is specific to the Claude Code PostToolUse hook, and Cursor and Codex users need to format on their own.

If you want migrations reviewed in Cursor and Codex too, add a plain-language line to `AGENTS.md` such as "review migrations for locks, reversibility and data loss". The subagent itself still only runs in Claude Code.

## Going forward

Edit `AGENTS.md` only. Do not paste its content into `CLAUDE.md` or `.cursor/rules`. If someone adds rules to `CLAUDE.md` above or below the import, move them to `AGENTS.md` unless they are Claude-specific.

One thing I did not do: I have not run the three tools to confirm each one picks up the file, so a quick check in each (ask "what Go version should I use?") is worthwhile.
