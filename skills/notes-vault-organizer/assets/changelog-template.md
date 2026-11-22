# Vault change log

Vault: <absolute path>
Backup: <commit hash or copy location>
Scan before: <file> (tree_sha256 <first 12 characters>)
Approved by the owner: <date, ids or categories, quoted words>

One block per change, appended as it happens. Moves are undone by moving the file back.

## m1

- Time: <ISO 8601 time>
- Kind: move
- From: <old path relative to the vault>
- To: <new path relative to the vault>
- Reason: <rule and reason from the plan>
- Check: destination exists, source gone
- Undo: move `<new path>` back to `<old path>`

## e1

- Time: <ISO 8601 time>
- Kind: edit (link text, tag rename or frontmatter)
- File: <path>
- Before: `<exact old text>`
- After: `<exact new text>`
- Undo: put the Before text back in that file

## Closing

- Scan after: <file> (tree_sha256 <first 12 characters>)
- Counts before and after: <broken links, orphans, notes>
- Not applied: <ids declined or left open>
