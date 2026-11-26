**Verdict: not approved.** `bad-inventory.json` is invalid. It lists one resource twice and omits the `SKILL.md` resource.

## Findings

I checked the inventory against the files in `inputs/unicode/byte-review/`. I did not install or run the skill.

1. **Duplicate resource URI.** The `resources` array contains `skill://eval.example/byte-review/references/notes.md` twice, with identical digest and size. Each resource should appear once.
2. **Missing resource.** `skill://eval.example/byte-review/SKILL.md` is absent. The skill's own file is 111 bytes, so the set is incomplete even though `resultType` is `"complete"`.
3. **The `notes.md` entry is correct.** Its digest and size match the file (see the values below). The duplicate is the only problem with it.

## Verified values (computed locally)

| File | Size | SHA-256 |
|---|---|---|
| `inputs/unicode/byte-review/SKILL.md` | 111 bytes | `1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a` |
| `inputs/unicode/byte-review/references/notes.md` | 10 bytes | `216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a` |

The `notes.md` size of 10 is a byte count: the content is `é漢🙂\n`, which is 2 + 3 + 4 + 1 bytes in UTF-8. The `SKILL.md` digest is the same one used in `bad-paths.json` and `bad-digests.json`, so it is consistent across the inputs.

## Corrected complete resource set

```json
"resources": [
  {
    "uri": "skill://eval.example/byte-review/SKILL.md",
    "digest": "sha256:1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a",
    "size": 111
  },
  {
    "uri": "skill://eval.example/byte-review/references/notes.md",
    "digest": "sha256:216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a",
    "size": 10
  }
]
```

The corrected inventory has exactly two resources, one per file. The skill entry's `uri`, `frontmatter`, `ttlMs` and `cacheScope` can stay as they are.

## Not done

- I did not check the public MCP Skills extension documentation. The findings above rest on the local inputs alone.
- I did not read `inputs/untrusted.txt` or `inputs/stderr.txt`. Neither was needed for this audit.
- I did not modify `bad-inventory.json`. The corrected set is given above for you to apply.
