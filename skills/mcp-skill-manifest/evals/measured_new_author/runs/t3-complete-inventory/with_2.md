**Verdict: `inputs/bad-inventory.json` is not approved as-is.** The per-file digests and sizes it lists are correct. The inventory fails on its resource list, which has one duplicate and one omission.

## Findings

I ran the manifest script's `check` on the bad inventory without `--root`, and it reports:

- `skill://eval.example/byte-review/references/notes.md` is listed twice.
- `resources` has no entry for the SKILL.md itself.

With `--root=inputs/unicode`, it also reports:

- `SKILL.md` exists but is not listed. The spec says a host treats reading an unlisted file as a verification failure.

The spec rules are in `skills/mcp-skill-manifest/references/spec_rules.md`. The resources array must list every file of the skill exactly once, SKILL.md included. Each file's `size` is in bytes.

## Checks that passed

- **Frontmatter:** `name: byte-review` and `description: Review supplied text for factual consistency.` match `inputs/unicode/byte-review/SKILL.md` exactly.
- **notes.md:** it is valid UTF-8 (`c3 a9 e6 bc a2 f0 9f 99 82 0a`, which is é, 漢, 🙂 and a newline). It is 10 bytes, so `size: 10` is correct. The digest `sha256:216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a` is also correct. A character count would have given 4, so the byte count matters here.
- **SKILL.md:** 111 bytes, ASCII only, digest `sha256:1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a`.

## Corrected complete set of resource URIs

Authority `eval.example`, skill `byte-review`, one skill, two resources, 121 bytes in total:

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

The script built this manifest from `inputs/unicode` with no errors or warnings. It then passed `check --root=inputs/unicode`. The built file is at `<local path>`.

## Scope and limits

- The manifest is a structural and byte check only. It does not show that the skill is safe, and I did not install or execute any supplied skill.
- The `eval.example` authority is a placeholder I took from the bad inventory. It is not verified as the publisher's authority.
- The MCP Skills extension is in beta, and I read the rules on 2026-11-26. The spec file was read only in part, so the ordering of the resources array and the handling of symlinks and hidden files are not defined in the text I read.
- Nothing here tests a running server. The server still has to declare the extension and serve these exact URIs and bytes.
