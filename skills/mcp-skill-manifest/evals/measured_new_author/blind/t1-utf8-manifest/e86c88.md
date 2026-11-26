The `skills/list` result for `inputs/unicode` is below. I did not install or run either skill. The byte sizes and digests come from `wc -c`, `od`, and `sha256sum` on the files, not estimates.

**Scope:** `inputs/unicode/` contains one skill, `byte-review`, with two files. I found no "authority" or "eval.example" field in the inputs, so I did not add one. I read only the supplied files and did not consult the MCP Skills docs.

```json
{
  "skills": [
    {
      "name": "byte-review",
      "description": "Review supplied text for factual consistency.",
      "source": "inputs/unicode/byte-review/SKILL.md",
      "files": [
        {
          "path": "SKILL.md",
          "bytes": 111,
          "sha256": "1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a"
        },
        {
          "path": "references/notes.md",
          "bytes": 10,
          "sha256": "216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a"
        }
      ]
    }
  ]
}
```

**Exact `references/notes.md` values:**
- Size: **10 bytes**
- SHA-256: **216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a**
- Raw bytes: `c3 a9 e6 bc a2 f0 9f 99 82 0a`, which is `é漢🙂` followed by a LF. The 10 bytes are 2 (é) + 3 (漢) + 4 (🙂) + 1 (LF).

**Other files checked:**
- `SKILL.md` is 111 bytes with SHA-256 `1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a`. It has LF line endings, no BOM, and no hidden characters. My own hand count came to 109 bytes, which the byte dump disproved, so the 111 figure is the one to rely on.
- Content of `SKILL.md`:
  ```
  ---
  name: byte-review
  description: Review supplied text for factual consistency.
  ---
  Review the supplied text.
  ```

**Checkable with:** `sha256sum` and `wc -c` (or `od -A d -t x1 -c`) on the two files above. The digests are of the files as they exist in `inputs/unicode/byte-review/`.
