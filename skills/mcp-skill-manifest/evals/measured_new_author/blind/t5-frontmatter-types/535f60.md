**Verdict: the frontmatter does not match.** The resource digest and size match, but the frontmatter has four discrepancies (two value/type mismatches, one missing key, one numeric-type mismatch).

**Digest and size (match)**
- `inputs/typed/typed-review/SKILL.md` is 128 bytes.
- SHA-256 is `05af98bd24c089ffe8203ce5046b223cd113654a1cac7d9beeaeff95793e815e`, which equals the manifest's `resources[0].digest`.

**Frontmatter, field by field**

| Path | Manifest (JSON type) | SKILL.md (YAML type) | Result |
|---|---|---|---|
| `name` | `"typed-review"` (string) | `typed-review` (string) | match |
| `description` | `"Review evidence."` (string) | `Review evidence.` (string) | match |
| `metadata.enabled` | `1` (number, integer) | `true` (boolean) | **mismatch: value and type** |
| `metadata.count` | `1.0` (number, float) | `1` (integer) | **mismatch: type only** (equal value) |
| `metadata.version` | absent | `"1.0"` (quoted string) | **missing from manifest** |

**Discrepancies to list**
1. `metadata.enabled`: manifest `1` (number) vs file `true` (boolean). Different type and different value.
2. `metadata.count`: manifest `1.0` (float) vs file `1` (integer). Same numeric value, different type. Per your instruction I do not treat these as equal.
3. `metadata.version`: present in the file as the string `"1.0"`, absent from the manifest.
4. Manifest `frontmatter` has no `version` key, so the manifest does not describe the file's full frontmatter.

The manifest's JSON types were confirmed by parsing it: `enabled` is `int` 1 and `count` is `float` 1.0. The file's `SKILL.md` body is `Review evidence.`; the manifest has no body field, so I did not compare it.

I did not install or run the skill, and I did not need the MCP Skills documentation for this comparison.
