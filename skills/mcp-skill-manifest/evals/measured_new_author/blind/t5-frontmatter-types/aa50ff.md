**Result: the frontmatter does not match.** The digest and size match, but three fields under `metadata` differ. The check script reports only `metadata` as differing; the field-level comparison below is mine.

**Byte-level match (passes)**
- `inputs/typed/typed-review/SKILL.md`: 128 bytes, `sha256:05af98bd24c089ffe8203ce5046b223cd113654a1cac7d9beeaeff95793e815e`.
- Manifest resource entry: `size` 128, `digest` `sha256:05af98bd24c089ffe8203ce5046b223cd113654a1cac7d9beeaeff95793e815e`. Both match.

**Frontmatter discrepancies**

| Field | SKILL.md (YAML) | typed-manifest.json | Discrepancy |
|---|---|---|---|
| `metadata.version` | `"1.0"` (string) | absent | Dropped field |
| `metadata.enabled` | `true` (boolean) | `1` (integer) | Type changed; 1 and true are different values |
| `metadata.count` | `1` (integer) | `1.0` (float) | Type changed; the value is numerically equal but the type differs |

Fields that match, with type: `name` = `"typed-review"` (string) and `description` = `"Review evidence."` (string).

Per the skill's frontmatter rule, the `count` case is a mismatch even though 1 and 1.0 are numerically equal. The host would reject this skill for frontmatter mismatch and must not load it.

**Script output**
` check inputs/typed-manifest.json --root=inputs/typed --authority=eval.example` returned `ok: false` with one error: `frontmatter differs from SKILL.md in field(s): metadata`. Skills: 1, files: 1, bytes: 128.

**What the manifest needs**
Rebuild the manifest from the SKILL.md bytes so its frontmatter carries `metadata.version` = `"1.0"`, `metadata.enabled` = `true`, and `metadata.count` = `1`. Then run `check` again. Do not edit the fields by hand.

**Limits of this check**
- The extension is in beta. This is a byte and metadata check only. It does not show the skill is safe or trusted.
- I ran the skill's `check` script read-only with `python -I`. I did not install or execute the supplied skill.
- I did not check the server's live bytes, `skills/get`, or `resources/read`. Those remain the server's job.
