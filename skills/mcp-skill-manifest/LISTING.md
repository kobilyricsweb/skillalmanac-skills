# Listing page content: mcp-skill-manifest

**One line:** Builds and checks the `skills/list` manifest that an MCP server needs in order to serve Agent Skills: every file's URI, sha256 digest and size in bytes.

## What it does

The MCP Skills extension (beta) lets an MCP server offer skills to a host. The extension tells a host not to use a file whose digest or size differs from the manifest. This skill gives an agent a five-step procedure and one script that:

1. Builds a `ListSkillsResult` from a folder of skills, with one entry per skill.
2. Refuses folders that break the extension's rules or would give two skills one URI: a name that breaks the naming rules, two skills with one name, more than 512 files or more than 16 MiB in a skill.
3. Checks a manifest against the folder again, and reports a changed file, a file that is not listed, a listed file that is gone, and frontmatter that differs.
4. Validates the structure of a manifest someone else produced.

## Capabilities

- `scripts/skill_manifest.py build`: writes the manifest; nothing is written when there are errors
- `scripts/skill_manifest.py check`: structure only, or structure plus a re-read of the files with `--root`
- `references/spec_rules.md`: each rule the script applies, with the section of the extension it comes from

## When to use

You want to serve skills from an MCP server, publish skills over MCP, generate or validate a `skills/list` response, or find out why a host rejects a served skill.

## When not to use

Writing the MCP server itself. Deciding whether a skill is safe to install: no manifest check can show that. Checking the bytes a remote server actually returned (`remote-skill-integrity`). Testing whether a skill helps (`skill-lie-detector`).

## Requirements

Python 3.9 or newer, standard library only. PyYAML is used when installed; without it only the plainest frontmatter is read and anything else stops the run. No network.

## Tested

- Fixture tests: 47/47.
- Reviewed by an independent agent before measurement. The defects it found are fixed. Fixtures cover them, except Windows junctions and unreadable folders, which were not tested.
- Run on the 266 skills of this repository (4,827 files, this one included): the manifest built with no errors and passed the check against the folder.
- Measured on 8 frozen tasks written by a Codex collaborator (2 runs per arm, Haiku executor): LIFT_UNCONFIRMED with both graders, +14.1 and +15.6 points, 4 tasks won, 4 tied, none lost. Positive, not confirmed.
- Not tested against a running MCP server or host, and not on real user tasks.

## Limits

- The extension is in beta and can change. The rules were read on 2026-11-26; parts of the spec and schema files were read only as a summary. See `references/spec_rules.md`.
- A digest match shows the bytes are the ones listed. It does not show the skill is safe.
- URI percent-encoding, symlinks and hidden files are not defined in the text this skill was written from. The script's choices are stated in SKILL.md.
