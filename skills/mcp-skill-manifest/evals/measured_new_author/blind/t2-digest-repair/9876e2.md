The digest values in `bad-digests.json` are correct for the supplied `inputs/unicode` files, but both entries use the wrong format, so the file is still malformed. Nothing was changed in the source files.

**Verified against `inputs/unicode/byte-review/`**

| Resource | Size in file | Size in JSON | Actual SHA-256 | Actual MD5 |
|---|---|---|---|---|
| `SKILL.md` | 111 bytes | 111 ✔ | `1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a` | `f1f08ccdde6935e448c9e54bf85fec7a` |
| `references/notes.md` | 10 bytes | 10 ✔ | `216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a` | `d8c53bf264eaec5cb256481fe4f16a28` |

**Findings**

1. **`SKILL.md` digest is malformed (format only).** The value is `1C17F105…8079A`: bare hex with no algorithm prefix and in uppercase. The hex matches the file's SHA-256 when compared case-insensitively. The canonical form used in `inputs/valid.json` is `sha256:` followed by lowercase hex.
2. **`references/notes.md` digest uses the wrong algorithm.** The value is `md5:d8c53bf264eaec5cb256481fe4f16a28`. The MD5 is correct for the file's bytes, but the other resource and the canonical format use SHA-256. The mixed algorithms are the defect.
3. **Sizes are correct.** Both match the byte counts.

**Corrected values** (computed from the files, and identical to the entries in `inputs/valid.json`):

- `SKILL.md`: `"digest": "sha256:1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a"`
- `references/notes.md`: `"digest": "sha256:216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a"`

**Checks you can rerun**

- `notes.md` is 10 bytes: `é` (2) + `漢` (3) + `🙂` (4) + LF (1).
- `SKILL.md` is 111 bytes, with `---` frontmatter, `name: byte-review`, and a one-line body.

**Limits**

- I could not check the public MCP Skills extension spec. The web search was denied permission. The `sha256:` lowercase-hex convention comes from `inputs/valid.json`, the only reference format in the supplied inputs.
- I did not install or execute any skill; I only read and hashed the files.
