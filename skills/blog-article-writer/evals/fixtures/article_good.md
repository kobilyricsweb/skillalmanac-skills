# Release notes your users will actually read

Most release notes are written for the team that shipped the work. Readers want to know one thing: what changed for me? This article shows a four-line template, a rule for ordering entries, and a test you can run in five minutes on your last release.

## Lead with the user's problem, not your ticket

Engineers log changes by ticket. Users remember them by pain. A line such as "Refactor queue worker (#412)" tells a customer nothing, while "Exports no longer time out on very large accounts" tells them the exact problem went away.

Try the swap on one real entry. Take the ticket title, then ask what the person was doing when the old behaviour got in their way. Write that sentence first and put the ticket number last, in brackets, for the team.

A team in the [2025 support survey](https://example.com/survey-2025) reported that 62% of release-note readers stopped after the first three entries. That makes the first three lines the whole release for most people.

## Order entries by how many people feel them

A flat list sorted by date buries the important change. Sort by reach instead: the entry that touches the most users goes first, bug fixes that affect everyone come next, and edge cases go last.

For example, in a release with eleven entries, a login fix that affects every account belongs above a new option in the admin panel that three customers asked for. Reach is a rough guess, and a rough guess still beats chronology.

Keep a hard cap of seven entries in the main list. Anything beyond that moves to a "Smaller changes" section at the bottom, collapsed or linked. Readers can see that more exists without wading through it.

Our [guide to changelog formats](/guides/changelog-formats) compares three layouts if you need one to copy.

## Say what the user should do next

Every entry ends in one of three states: nothing to do, something to check, or something to change. Say which. "Nothing to do" is a useful sentence, because it removes a worry.

Suppose a release changes the default date format. The entry should read: "Dates now show as 2026-11-21. If you parse dates from exports, update your parser by 1 December." The deadline and the action sit in the same sentence as the change, so nobody has to open a second page.

Breaking changes get their own heading and appear first, always. Put the date the old behaviour stops working in the heading, and link to the migration steps in the [upgrade checklist](/docs/upgrade-checklist).

## Test the notes on someone who did not build the release

Hand the draft to a person from support or sales and ask them to explain each entry aloud in one sentence. Where they hesitate, the entry is written for engineers.

Time the exercise. If it takes longer than five minutes for seven entries, the notes are too dense. In one review of ten releases, entries over 30 words drew the most questions, according to the [analysis by the docs team](https://example.com/docs-team-analysis). Shorter entries drew fewer.

Then run the final pass: one change per line, no internal jargon, a date on every deadline, and the biggest change first. Ship it when all four hold.
