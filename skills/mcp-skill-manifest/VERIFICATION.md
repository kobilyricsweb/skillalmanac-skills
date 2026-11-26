# Verification

All runs on 2026-11-26.

## 1. Does the skill help? Positive, not confirmed

**Headline: LIFT_UNCONFIRMED with both graders.** The skill won 4 of 8 tasks, tied 4 and lost none. That is a positive result that the test's own rules do not confirm.

- **Tasks:** 8 tasks with 32 checks, written by a Codex collaborator (a different author and model family, who also reviewed this skill, so not an external party). They were frozen before any run (tasks.json SHA-256 `7d969dea51e2f189e54982423883cd6490859c7b7da492ee748c7d2463c181be`) and run unchanged. They are synthetic, not real user tasks.
- **Setup:** claude-haiku-5-5, 2 runs per arm, each in a fresh `claude -p` session and a fresh folder holding the same input files. In the without arm the skill folder was not present. Neither arm had web access, so the with-skill arm's only extra knowledge was this skill.
- **Grading:** identity words (the skill and script names, local paths) were deleted from the answers. Each grader got one task's answers in the prompt, in a fresh session with all tools disallowed.
- **Version measured:** tree digest `94596ab0f686273745a5097a905d84dd70b29f25221b31ac6fbb6f1deaa7dd96` over the 6 files of the skill before the evidence folder was added.

| Grader | Verdict | Mean difference | 95% interval | Sign-flip p (two-sided) | Won / tied / lost |
|---|---|---|---|---|---|
| claude-sonnet-5-5 | LIFT_UNCONFIRMED | +14.1 points | +3.1 to +25.0 | 0.125 | 4 / 4 / 0 |
| claude-opus-5-5 | LIFT_UNCONFIRMED | +15.6 points | +3.1 to +28.1 | 0.125 | 4 / 4 / 0 |

- **Why it is not confirmed:** four tasks tied at 100% in both arms, so only four tasks carry information. With four tasks, even a clean sweep gives a two-sided p of 0.125.
- **Where the skill helped:**
  - Building a manifest for files with non-ASCII text: 100% vs 75%.
  - Finding what changed after a manifest was built: 100% vs 75%.
  - Applying the size limits: 100% vs 75%.
  - Trust and dynamic content: 87.5% or 100% vs 50%.
- **Where it made no difference:** repairing malformed digests, completing a file inventory, frontmatter types and URI containment. The plain model scored 100% on all four.
- **Grader agreement:** 128 of 128 check results.
- **Blinding limit:** after redaction, `blind.py` still lists terms found in at least half of one arm's answers and in none of the other's: beta, errors, build, extension beta, warnings, the script, uris and. A grader can often guess the arm.
- **Cost:** answers with the skill were longer (3,094 vs 2,668 characters on average).

Files: `evals/measured_new_author/` (tasks, inputs, runs, blinded copies, key, both graders' grades and verdicts).

## 2. Scripts (fixtures)

Command: `python evals/run_fixtures.py`. Result: 47/47 passed. The cases cover:

- **Build:** a clean build, byte sizes for non-ASCII text, raw sha256 digests, and the exclude and nested options.
- **Check against the folder:** an edited file, same-size different bytes, changed line endings, an unlisted file, a missing file, changed frontmatter, and frontmatter types compared strictly.
- **Refusals:** a bad name, a duplicate name, more than 512 files, more than 16 MiB, no frontmatter, NaN, a non-string key, a non-UTF-8 SKILL.md, and a manifest written inside the skills root.
- **Manifests from elsewhere:** a missing SKILL.md entry, wrong digest forms, missing resources, a file outside the skill, URIs that leave the skill folder, a URI with no scheme, a non-object entry, and a wrong cache scope.
- **The fallback YAML reader:** the same result as PyYAML on plain frontmatter, and a stop on anything else.

## 3. A run on real skills

`build` and then `check --root` on the 266 skill folders of this repository (4,827 files, 16.45 MB): no errors and no warnings.

## 4. Independent review

A separate agent reviewed the script and the documents before the measurement and found 14 defects. All are fixed:

- `check` accepted URIs that leave the skill folder.
- The fallback YAML reader returned different values than PyYAML without warning.
- An indented `---` inside block text closed the frontmatter early.
- Non-ASCII output crashed on a Windows console.
- An unreadable subfolder was skipped without an error.
- `--exclude` did not apply to nested discovery.

The Codex collaborator found two wording defects, fixed before the measured version was frozen:

- A referral that implied another skill can judge safety.
- A line that treated key order as a frontmatter mismatch.

## Not tested

- A running MCP server or host.
- Real user tasks.
- Agents other than Claude Code, and executors other than claude-haiku-5-5.
- Windows junctions and unreadable folders (fixed in code, no fixture).
- The parts of the extension spec that were read only as a summary. See `references/spec_rules.md`.
