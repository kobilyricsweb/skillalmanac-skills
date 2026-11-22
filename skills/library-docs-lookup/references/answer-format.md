# Answer format for library questions

Use this shape for every answer that rests on a library's behaviour. Keep it short; the evidence is the point.

```
Verdict: <LOCAL-VERIFIED | LOCAL-ABSENT | CHANGELOG-ONLY | UNVERIFIED> - <one sentence answer>
Package: <name> <resolved_version> (<resolved_from>)
Evidence:
- <path>:<line> - <what that line shows, quoted or paraphrased in a few words>
- <path>:<line> - ...
Version notes: <mismatch between lock and installed, changelog entries in range, or "none">
Not checked: <e.g. runtime behaviour, other import paths, type checker not run>
```

## Label rules

| Label | Use only when |
|---|---|
| `LOCAL-VERIFIED` | You read the symbol's definition or documentation in a file of the installed package during this task, and cite its line. |
| `LOCAL-ABSENT` | You searched the types, the entry file and the package folder for the name and found nothing. Say which places you searched. Offer likely real names only if they appear in those files. |
| `CHANGELOG-ONLY` | A local changelog states it (renamed, removed, default changed) but you did not see the code. |
| `UNVERIFIED` | Nothing local was available (not installed, or a package type the script does not cover). Say what you would have read. |

## Evidence rules

- Cite a line number you saw in tool output. A range (`index.d.ts:41-58`) is fine for a multi-line signature.
- One evidence line per claim. Two claims from one file get two lines if they sit in different places.
- Quote at most a signature or one short line; do not paste long blocks of a package's text into the answer.
- Put the version next to the package even when it was unchanged from earlier in the conversation, so the answer stands alone.
- When the user's existing code uses a name that the evidence contradicts, say which line contradicts it before proposing the fix.

## When the answer is "it does not exist"

State `LOCAL-ABSENT`, the version, and the places searched. Then, only from names present in the searched files, list the closest real exports. If the changelog shows the name was removed or renamed, add the version where that happened and switch the label to `CHANGELOG-ONLY` for that part.
