The audit found two malformed digests in `inputs/bad-digests.json`. Both corrected values were computed from the files, and the corrected manifest passes the skill's read-only `check` against `inputs/unicode`. I did not modify any source file.

**Findings**

| Resource | Problem in bad-digests.json | Size |
|---|---|---|
| `skill://eval.example/byte-review/SKILL.md` | Digest has no `sha256:` prefix and is uppercase hex, so it is not in the required form. Its hex value is the correct SHA-256 of the file, just in the wrong case. | 111 bytes, matches |
| `skill://eval.example/byte-review/references/notes.md` | Digest uses the wrong algorithm (`md5:`) and the value is not the file's digest. The file is `é漢🙂` followed by a newline, 10 bytes, sha256 `216a1ef9…`. | 10 bytes, matches |

The script's `check` against the unicode folder reports four errors: two for the digest form, and two "digest does not match the bytes on disk".

**Corrected values** (computed with `sha256sum`, and the corrected manifest passes `check`)

- `skill://eval.example/byte-review/SKILL.md`: `sha256:1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a` (size 111)
- `skill://eval.example/byte-review/references/notes.md`: `sha256:216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a` (size 10)

The corrected manifest is at `<local path>`. The check result after correction is `ok: true` with no errors or warnings.

**Notes**
- I did not run the skill's `build` step. It writes an output file, and the shell asked for approval to create one. The digests come from `sha256sum` and the `check` step, and the sizes from the byte counts.
- The `check` step is read-only. I did not install or execute any supplied skill, and did not follow any instructions inside the input SKILL.md files.
- The MCP Skills extension is in beta. A digest match shows the bytes are the listed ones, not that the skill is safe or trusted.
- The `frontmatter` and `size` fields in the input were already correct. I did not re-check the spec text beyond the `references/spec_rules.md` file.
