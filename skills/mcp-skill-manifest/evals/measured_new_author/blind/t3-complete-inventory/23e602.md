**Verdict: `inputs/bad-inventory.json` is not approved.** It has two defects. Its digests and sizes are correct, and only the resource list is wrong.

**Findings**

1. **Duplicate resource URI.** `skill://eval.example/byte-review/references/notes.md` appears twice (lines 12–15 and 17–20), with identical digest and size. A resource inventory must list each URI once, and a duplicate makes the entry ambiguous.
2. **Missing `SKILL.md` resource.** The inventory never lists `skill://eval.example/byte-review/SKILL.md`, even though the skill's own `uri` points at that file. `inputs/valid.json` lists `SKILL.md` as a resource, so the bad inventory is incomplete.
3. **Digests and sizes are correct.** I checked the files on disk. `references/notes.md` is 10 bytes, `sha256:216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a`. Its bytes are `C3 A9` (é), `E6 BC A2` (漢), `F0 9F 99 82` (🙂), and `0A` (newline), which is 10 bytes. `SKILL.md` is 111 bytes, `sha256:1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a`. The non-ASCII content is not the problem; sizes must be counted in bytes.

I did not consult the public MCP Skills extension documentation. The findings rest on the supplied files: the duplicate is a set-semantics violation, and the missing entry is established by `valid.json`.

**Corrected complete inventory** (each URI once, `SKILL.md` included):

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

The corrected resource URIs are:
- `skill://eval.example/byte-review/SKILL.md`
- `skill://eval.example/byte-review/references/notes.md`

I only read and hashed the files. I did not install or run any supplied skill.
