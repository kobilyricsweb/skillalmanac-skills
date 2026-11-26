The `skills/list` result for `inputs/unicode` (authority `eval.example`) is below. I read the files and computed the sizes and digests from the bytes on disk. I did not install or run any skill, and I did not need the public MCP Skills docs because the supplied `valid.json` already shows the response shape.

**notes.md byte size and digest**
- Size: **10 bytes**. The content is `é漢🙂` followed by LF (2 + 3 + 4 + 1 = 10).
- SHA-256: **`216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a`**

**SKILL.md**
- Size: 111 bytes
- SHA-256: `1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a`

Both computed digests and sizes match the entries in `inputs/valid.json`.

**Files included.** `inputs/unicode/` contains exactly two skill files, and both are in the result:
- `byte-review/SKILL.md`
- `byte-review/references/notes.md`

**Result:**

```json
{
  "resultType": "complete",
  "skills": [
    {
      "uri": "skill://eval.example/byte-review/SKILL.md",
      "frontmatter": {
        "name": "byte-review",
        "description": "Review supplied text for factual consistency."
      },
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
    }
  ],
  "ttlMs": 300000,
  "cacheScope": "public"
}
```

**Scope notes**
- I only covered `inputs/unicode/`. The other fixtures (`drift/`, `typed/`, the `bad-*.json` files, `limits.json`) were not turned into results.
- `limits.json` sets a publisher policy of at most 512 files or 16 MiB per skill. This skill is 2 files and 121 bytes in total, so it is within that policy.
