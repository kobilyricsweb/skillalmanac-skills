**Verdict: the frontmatter does not match.** The digest and size match, but the frontmatter disagrees in three places. The file is `inputs/typed/typed-review/SKILL.md`, and the manifest is `inputs/typed-manifest.json`.

**Resource check (passes)**
- Manifest digest: `sha256:05af98bd24c089ffe8203ce5046b223cd113654a1cac7d9beeaeff95793e815e`
- Computed `sha256sum`: `05af98bd24c089ffe8203ce5046b223cd113654a1cac7d9beeaeff95793e815e`
- Manifest size: `128`. File size: `128` bytes.

**Frontmatter comparison**

| Field | Manifest (JSON) | SKILL.md (YAML) | Result |
|---|---|---|---|
| `name` | `"typed-review"` (string) | `typed-review` (string) | Match |
| `description` | `"Review evidence."` (string) | `Review evidence.` (string) | Match |
| `metadata.enabled` | `1` (number) | `true` (boolean) | **Mismatch: type and value** |
| `metadata.count` | `1.0` (number, written as a float literal) | `1` (YAML integer) | **Mismatch: literal type.** Both are 1 in value, but the manifest writes a float and the file an integer. JSON has one number type, so this only shows up if the distinction is kept. |
| `metadata.version` | absent | `"1.0"` (string) | **Mismatch: key missing from the manifest** |

**Discrepancy list**
1. `metadata.enabled`: manifest has number `1`; file has boolean `true`. Different type and value.
2. `metadata.count`: manifest has `1.0` (float literal); file has `1` (integer). Same numeric value, different type under the rule you set.
3. `metadata.version`: present in the file as the string `"1.0"`, absent from the manifest.

The file's body (`Review evidence.`) is not frontmatter, so I did not compare it. I did not install or run the skill. I checked the frontmatter by reading the file, not by parsing it with a YAML library.
