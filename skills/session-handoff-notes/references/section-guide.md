## Contents

- Header lines
- Goal
- Current state
- Changes made
- Verification
- Open decisions
- Next steps
- Commands
- Not verified
- Where to save and how to read one

# Section guide

Read only the section you are unsure about. Each entry gives the rule, a weak line and its repair.

## Header lines

Two lines under the title: `Written: YYYY-MM-DD` and `Repo state: branch X at commit HASH, N files modified`. The reader needs them to judge whether the repository has moved since. Take the hash from `git rev-parse --short HEAD` and the modified count from `git status --short`. Outside git, write `Repo state: no git, folder <path>`.

## Goal

The outcome and the condition that proves it. Weak: "Work on the cart." Repair: "Make `total()` return integer cents; done when `make test` exits 0." If the goal changed during the session, state the current goal and one clause on what it replaced.

## Current state

Facts true at the moment of writing, one per line. Include the half-finished item and the exact place where it stopped (file and function). Leave out history of attempts that led nowhere unless the next session would repeat them; then state it as a trap: "Do not use X, it fails with Y."

## Changes made

One bullet per file or per coherent change, each with the path in backticks. Weak: "Fixed stuff in the cart module." Repair: "`src/cart.py`: `total()` sums integer cents instead of float dollars." For deletions say why it was safe. Take the list from `git diff --stat` and `git status --short`, not from memory, and add changes the diff cannot show (a database row, an environment variable, a remote setting).

## Verification

A line is a command in backticks plus its result: exit code, pass and fail counts, or the key output line. A check that was skipped says "not run" and why. Weak: "Tests pass." Repair: "`make test` exited 0, 12 passed." Never write a success claim anywhere else in the note without the same evidence on that line. If a result came from an earlier session, say so and give its date.

## Open decisions

Each is a question, the options, a recommended default, and who must answer. Weak: "Decide about the PDF thing." Repair: "Should `billing/pdf.py` convert cents at render time or should `total()` change? Recommend render time; blocked on the owner." If there are none, write "None."

## Next steps

A numbered list in the order to do it. Step 1 must be something the next session can run or open without thinking, usually the command that re-establishes the baseline. Weak: "Look at the PDF code." Repair: "Open `billing/pdf.py` and convert cents to a display string only when rendering."

## Commands

Literal commands in a fenced block: start the environment, run the checks, show the diff, and any command that was hard to find out. Real values, no placeholders. Do not paste secrets; name where the value lives ("read from the password manager entry named in the team wiki").

## Not verified

What nobody checked: areas read but not run, paths with no test, assumptions taken from the user. A note that lists nothing here is usually overconfident.

## Where to save and how to read one

Save the note where the next session will look first: a file in the repository root or a docs folder, named with the date, for example `HANDOFF-2026-11-21.md`, and tell the user the path. Do not commit it unless asked. When reading a note, treat each claim as a lead: re-run the baseline command from step 1 of Next steps before trusting the Current state section.
