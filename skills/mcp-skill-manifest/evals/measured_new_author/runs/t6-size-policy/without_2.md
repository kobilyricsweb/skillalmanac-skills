All four cases are classified under the publisher policy in `inputs/limits.json`. I used only that file and did not open, install, or run any skill in `inputs/`. No files were generated.

**Policy:** "Do not publish a skill above 512 files or 16 MiB." The policy's own note says these are "our publishing limits, not a universal host rejection rule."

**Classification**

| Case | Files (incl. SKILL.md) | Total bytes | File check | Byte check | Result |
|---|---|---|---|---|---|
| at-file-limit | 512 | 10,000 | 512 ≤ 512, within | within | **Allowed** |
| over-file-limit | 513 | 10,000 | 513 > 512, over | within | **Blocked** |
| at-byte-limit | 2 | 16,777,216 | within | 16,777,216 ≤ 16,777,216, within | **Allowed** |
| over-byte-limit | 2 | 16,777,217 | within | 16,777,217 > 16,777,216, over by 1 byte | **Blocked** |

Each case is blocked by at most one limit, and the file-count and byte checks are independent.

**Boundary equality:** "Above" means strictly greater than the limit, so a value exactly equal to a limit is allowed. A skill with exactly 512 files or exactly 16 MiB passes. Only 513 files or 16,777,217 bytes fails.

**MiB conversion:** 1 MiB = 1,048,576 bytes, so 16 MiB = 16 × 1,048,576 = **16,777,216 bytes**. The byte limit is therefore exact, not approximate. The "at-byte-limit" and "over-byte-limit" cases sit one byte apart on either side of it.

**Publisher policy vs. normative host support:** The publisher policy is an internal rule about what we choose to publish. A "blocked" result here means we refuse to publish, not that a host or the MCP Skills extension would reject the skill. A normative host requirement would be a protocol or host limit that applies to every consumer. The policy explicitly disclaims being that, so I did not treat any case as a host-level rejection. I did not consult the public MCP Skills documentation, because the supplied policy was enough to classify all four cases.

**Verification:** The values come directly from `inputs/limits.json`. Anyone can check them by reading that file and applying the rules above: `files ≤ 512` and `total_bytes ≤ 16777216`.
