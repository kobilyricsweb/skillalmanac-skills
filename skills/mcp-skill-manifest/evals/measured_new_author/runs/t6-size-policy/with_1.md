## Classification (publisher policy)

The policy in `inputs/limits.json` says: "Do not publish a skill above 512 files or 16 MiB." Only counts are measured, so no files were generated, no manifest was built, and no skill was run.

| Case | Files (incl. SKILL.md) | Total bytes | File check (≤ 512) | Byte check (≤ 16 MiB) | Verdict |
|---|---|---|---|---|---|
| `at-file-limit` | 512 | 10,000 | Equal, allowed | Passes | **Publishable** |
| `over-file-limit` | 513 | 10,000 | Exceeds by 1 | Passes | **Not publishable** |
| `at-byte-limit` | 2 | 16,777,216 | Passes | Equal, allowed | **Publishable** |
| `over-byte-limit` | 2 | 16,777,217 | Passes | Exceeds by 1 byte | **Not publishable** |

Each failing case fails on one dimension only. The file count and byte total are checked independently, so a skill must pass both.

## Boundary equality

"Above" means strictly greater than. A value equal to the limit is allowed. The public-spec rules in `skills/mcp-skill-manifest/references/spec_rules.md` say the same thing: "At most 512 resources" and "At most 16 MiB (16,777,216 bytes)". So 512 files and exactly 16,777,216 bytes are inside both limits. The over-limit cases are only one step past, so an off-by-one at the boundary changes the verdict.

## MiB conversion

- 1 MiB = 1,048,576 bytes (2^20).
- 16 MiB = 16 × 1,048,576 = **16,777,216 bytes**.
- `at-byte-limit` (16,777,216 bytes) = exactly 16.0 MiB.
- `over-byte-limit` (16,777,217 bytes) = 16 MiB + 1 byte ≈ 16.00000095 MiB. It is over the limit by one byte.

The byte total should be a sum of raw file sizes in bytes, not characters. The skill's rules say so explicitly. I used `total_bytes` as supplied and did not check how it was measured.

## Publisher policy versus normative host requirements

- **Publisher policy (ours):** a publishing gate that this organization applies. `limits.json` says it is "our publishing limits, not a universal host rejection rule." It decides whether we publish. Here it is a hard gate for us.
- **Normative spec (MCP Skills extension, beta):**
  - The 512-file and 16 MiB figures are limits on what a skill may contain. Servers SHOULD NOT serve a skill over either one. That is a SHOULD NOT, not a MUST.
  - Hosts MUST NOT use content on a digest mismatch, size mismatch, unlisted file, or frontmatter mismatch. Hosts MUST NOT treat a digest match as a security boundary. Hosts MAY decline `"dynamic"` content. The rules I read do not give hosts a MUST to reject based on file count or total bytes.

So the two agree on the outcome for these cases, but for different reasons. A host could in principle load an over-limit skill that passes its digest and size checks. Our policy does not depend on that. Our policy stops us publishing such a skill regardless of what hosts do.

## Caveats

- The rules come from `spec_rules.md`, read on 2026-11-26. The extension is in beta, and I did not re-fetch the live spec in this session.
- No manifest was built. The `skill_manifest.py` script was not run, because no file generation was requested and nothing was executed.
- All findings come from the supplied `inputs/limits.json` and the skill's reference file. Nothing else was used.
