---
name: reviewing-code-changes
description: Reviews a diff, branch, commit or pull request for defects that matter (broken callers outside the diff, weakened tests, security holes, unsafe migrations, behaviour changes the description hides) and returns a short ranked verdict in which every finding is verified and has a concrete failure scenario. Use when the user asks for a code review, a PR review, a second pair of eyes, whether a change is safe to merge, or to check what an agent just wrote. Do not use to write the change, write tests, explain code, or review prose, contracts or designs with no diff.
license: Apache-2.0
compatibility: Tool-neutral. Works best with a checked-out repo so callers and tests can be inspected and run. The diff map script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Reviewing code changes

A review is worth what its findings are worth. One verified defect with a failing input beats ten suspicions. The reader should be able to act on every line of the review without re-investigating it, and should finish it in two minutes.

The diff shows what changed. Most serious defects are in what did not change: the caller that still expects the old behaviour, the test that no longer checks anything, the table that already has rows.

## Workflow

### 1. Get the change and the claim

Obtain the diff (a file, `git diff <base>...HEAD`, or the PR) and the description. Write down, privately, each claim the description makes ("no behaviour change", "pure refactor", "adds index"). Each claim is something to verify, and a false claim is itself a finding.

### 2. Map it

```bash
python scripts/diff_risk_map.py change.diff
git diff main...HEAD | python scripts/diff_risk_map.py -
```

Run the script, do not edit it. It lists files by risk, the symbols and constants whose definitions changed, and signal lines (removed or weakened tests, swallowed errors, string-built SQL, risky schema statements, changed numeric values, skipped tests, debug leftovers). Signals are leads to confirm, and silence is not a pass. Without Python, read the diff once for the same list.

Read in risk order: schema and data migrations, auth and money paths, public interfaces, then the rest, tests last but always.

### 3. Leave the diff

For every symbol whose **signature, return value, units, default, error behaviour or meaning** changed, search the repo for every use, including files the diff does not touch, re-exports and aliases, dynamic references, config and deploy files, and other languages or clients that consume the same interface. Open each use and decide whether it still holds. A changed function with an unvisited caller is an unfinished review.

For every new code path, find its siblings (other routes in the router, other handlers in the module) and compare: what guard, validation, transaction, logging or error handling do they have that the new one lacks? The repo's own pattern is the standard.

For a schema change, find the facts the diff cannot show: is the table already populated, how large, and which code reads or writes the column in the same release.

### 4. Check the tests as evidence

- Compare removed and added assertions. An exact check replaced by "is not None", "is truthy" or "does not throw" is a weakened test. A deleted test is a finding unless the behaviour it covered is gone.
- Ask of each new test: would it fail if the change were wrong? A test that passes before and after proves nothing about the change.
- Run the test suite when the repo allows it and say what ran. Passing tests do not clear the change; note what they do not cover.

### 5. Prove each serious finding

Before a finding is reported as blocking, make it concrete:

1. The exact line (file and line number), quoted.
2. A specific input or situation, and the wrong outcome it produces.
3. Where possible, **run it**: a one-line call, a short script in a scratch location, or the existing test adapted, and quote the output. "Gold invoice of 20000 returns 19970.0, expected 17000" ends the discussion; "this might break invoices" starts one.

If a suspicion cannot be made concrete after looking, either drop it or put it under Questions as a question. Do not pad the review with possibilities.

For the patterns worth checking by change type (request handlers, data access, migrations, refactors, concurrency, money and time), read the matching section of [references/defect-patterns.md](references/defect-patterns.md).

### 6. Rank and cut

- **Blocking**: wrong results, data loss or corruption, security exposure, an outage on deploy, a contract broken for an existing caller.
- **Should fix**: real defects with limited reach, missing tests for new behaviour, a description that misstates the change.
- **Notes**: at most three. Only things the author would thank you for. Nothing a formatter or linter enforces, no naming preferences, no praise.

Merge duplicates: one root cause is one finding, however many lines show it. Order by severity, then by how certain the finding is.

### 7. Write the review

```
Verdict: <Do not merge | Merge after fixes | OK to merge> - <one sentence why>

Blocking
1. <file>:<line> - <what is wrong, one line>
   Fails when: <input or situation> -> <wrong outcome> (<verified by: command and output | read>)
   Fix: <specific change>

Should fix
2. ...

Notes
- ...

Questions
- <only what the code cannot answer>

Checked: <tests run and result; callers searched for which symbols; files read outside the diff>
Not checked: <what could not be verified, such as production data, other services, performance>
```

Rules for the write-up:

- The verdict comes first and matches the findings: any Blocking item means the verdict is not an approval.
- Every finding has a location and a "Fails when". No finding is a paragraph.
- Suggest the smallest fix that follows the repo's existing pattern; name the helper or middleware to use.
- Omit empty sections. A clean change gets a short review; do not manufacture findings to seem thorough.
- Do not restate the diff or narrate the review process.

## Limits

- Without the repo, callers and tests cannot be checked; say so at the top and treat the review as partial.
- The script reads diff text. It does not parse the languages, so it misses renamed symbols and anything that needs understanding of the code.
- A review does not replace running the change against production-like data or load.
- Findings reflect the code as read at review time; if the branch moves, the review is stale.
