All four cases are classified from `inputs/limits.json`. Nothing was installed or executed, and no files were generated.

**Policy (from the file):** "Do not publish a skill above 512 files or 16 MiB. Treat these as our publishing limits, not a universal host rejection rule."

| Case | Files (incl. SKILL.md) | Total bytes | File check | Byte check | Result |
|---|---|---|---|---|---|
| at-file-limit | 512 | 10,000 | 512 ≤ 512 → pass | 10,000 ≤ 16,777,216 → pass | **Allowed** |
| over-file-limit | 513 | 10,000 | 513 > 512 → fail | pass | **Rejected** (file count) |
| at-byte-limit | 2 | 16,777,216 | pass | 16,777,216 ≤ 16,777,216 → pass | **Allowed** |
| over-byte-limit | 2 | 16,777,217 | pass | 16,777,217 > 16,777,216 → fail | **Rejected** (bytes) |

**Boundary equality:** The policy says "above" the limit is disallowed, so a value equal to the limit is permitted. The two "at" cases are allowed, and the two "over" cases are rejected by exactly one unit.

**MiB conversion:** 16 MiB = 16 × 1,048,576 = 16,777,216 bytes. The policy specifies MiB (binary), not MB (decimal). If someone read 16 MB as 16,000,000 bytes, the at-byte-limit case (16,777,216) would wrongly be rejected. The over-byte case is 1 byte above the binary limit.

**Publisher policy vs. host support requirements:** The policy is the publisher's own gate on what this team will publish. Its last sentence says it is "not a universal host rejection rule," so it does not claim that a host would reject a 513-file or 16 MiB+1 skill. A normative host requirement would be a limit the host must enforce, stated in the protocol spec. I did not consult the public MCP Skills extension documentation, so I can't say what the host's own limits are. This classification applies only to the publisher policy.
