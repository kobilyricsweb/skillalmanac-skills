# Rewrite table and never-include list

Read the audience table before the first rewrite, and the never-include list before delivering.

## Audience split

Pick one audience per document and say which in the report. Two audiences means two documents.

| Audience | Sections kept | Wording | Length per entry |
|---|---|---|---|
| End users | Breaking, Added, Changed, Removed, Fixed, Security, Performance | The visible effect, in the product's own nouns | One sentence |
| Developers or integrators | All of the above plus Documentation and Internal; scopes kept; issue numbers kept | API, flag and config names exactly as written | One to two sentences; breaking entries may be longer |
| Operators | Breaking, Security, Changed, Removed, and anything that touches configuration, ports, schema or upgrade order | What must be done before, during, after the upgrade | As long as the steps need |

## Rewriting internal wording

The rewrite states what a user can now do, no longer suffers, or must now do differently. If the commit gives no visible effect, the entry is Internal: drop it from user notes. If it might have a visible effect, ask.

| Commit wording | Problem | Rewrite or action |
|---|---|---|
| refactor the report handler | Names an implementation | Drop for users. Ask only if the commit body mentions behaviour. |
| fix race in cache invalidation | Cause, not effect | Ask: "What did a user see?" Then "Fixed stale results appearing after an edit" (only if confirmed). |
| add helper for date parsing | Implementation | Drop, or merge with the feature that uses it. |
| fix crash on empty input | Vague object | Ask which screen or command; write "Fixed a crash when exporting an empty report". |
| bump dependency x to 4.2 | Internal unless it fixes something users saw | Drop; if the commit says it closes a vulnerability, use the Security rule. |
| improve performance | No number, no place | Ask where and how much. Quote a figure only if the user supplies a measurement. |
| misc cleanup, tweaks, stuff | Carries no information | Unsorted: ask. |
| add `--dry-run` flag to deploy | Already visible | Keep: "Added a `--dry-run` option to `deploy` that shows what would change without changing it" (the second half only if the commit says so). |

Rules of thumb:
- Lead with the verb users care about (can, no longer, now). One change per line.
- Use the name the product shows on screen, not the module name.
- Keep issue or PR numbers only for audiences who can open them (developers, public repos).
- Keep tense consistent within a section: past tense for Fixed, present or past for Added, but not mixed.

## Never include

| Item | Why | What to do instead |
|---|---|---|
| Secrets, tokens, keys, internal hostnames, private URLs | Notes are copied and indexed | Remove; tell the user if a commit message contained one (it should be rotated) |
| Author emails or personal names (unless the user wants credits) | Privacy | Credit by handle only on request |
| Ticket IDs from a private tracker | Dead links for readers | Describe the change in words |
| Customer or tenant names | Confidentiality | Say "a customer-reported issue" only if true |
| Unreleased or unannounced feature names, flags still off | Premature disclosure | Leave out; list under a "held back" line in the report to the user |
| CVE identifiers or exploit detail before a fix ships | Gives attackers a head start | Ask the user; publish after the fixed version is available |
| Performance numbers nobody measured | Claims that cannot be backed | Omit the number |
| Commit hashes for non-developer audiences | Noise | Omit |
| Internal reverts and their targets | They never reached users | Both dropped (the script does this) |
| Wording from the commit that is blame or frustration ("finally fix the stupid bug") | Tone | Neutral rewrite |
| A guessed effect, migration step or date | Fabrication | `[FILL]` and ask |

## Breaking entry template

```
- <What changed, in one sentence> (<version or scope if useful>)
  - Who is affected: <which users, versions, configurations>
  - What to do: <steps, or "no workaround; this removes X">
```

Order inside the Breaking section: removals first, then renamed or changed interfaces, then changed defaults.
