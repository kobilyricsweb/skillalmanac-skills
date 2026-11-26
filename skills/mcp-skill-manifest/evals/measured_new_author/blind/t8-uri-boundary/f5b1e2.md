## Audit of `inputs/bad-paths.json`

**Verdict: reject this skill entry.** It has two defects: the frontmatter name does not match the URI, and one resource URI escapes the skill's own directory. The digest fields were ignored as you asked. I did not install or run anything, and I did not consult the public MCP Skills documentation, so the rules below come from the supplied inputs and general URI rules (RFC 3986).

### 1. Frontmatter name vs. SKILL.md URI

| Field | Value |
|---|---|
| `frontmatter.name` | `byte-review` |
| SKILL.md `uri` | `skill://eval.example/wrong-name/SKILL.md` |
| Directory segment | `wrong-name` |

The name does not match the directory segment. The baseline `valid.json` entry has `name: "byte-review"` and the URI `skill://eval.example/byte-review/SKILL.md`, so in the supplied fixtures the name and the directory segment match. This entry breaks that pattern. The file name `wrong-name` suggests the mismatch is deliberate.

I did not check this against the spec's exact name rule, so treat it as a fixture inconsistency that the audit should reject, not as a confirmed quotation of a requirement.

### 2. Resource containment escape

The SKILL.md resource is contained: `skill://eval.example/wrong-name/SKILL.md`.

The second resource is not:

- `skill://eval.example/wrong-name/%2e%2e/private.txt` (size 7)

- **Raw segments:** `["skill:", "", "eval.example", "wrong-name", "%2e%2e", "private.txt"]`. A literal check for a `..` segment does not match `%2e%2e`.
- **After percent-decoding:** `%2e` is the unreserved character `.` (RFC 3986 §2.3), so the segment becomes `..`. RFC 3986 normalization is required to decode unreserved percent-encodings before comparing URIs (§6.2.2.2).
- **After dot-segment removal** (§5.2.4): `skill://eval.example/private.txt`.
- That path is outside the skill directory `skill://eval.example/wrong-name/`, so containment fails.

I worked this out by hand. Python is not installed here (the `python3` alias failed), so no script ran.

A resolver that checks for raw `..` strings and skips decoding would accept this resource. A resolver that decodes and then normalizes would resolve it to a sibling of the skill directory.

### 3. Why a server URI authority is not publisher authentication

Both entries use the authority `eval.example`. The authority is part of the name the server gives the resource. It does not prove who published the content:

- **Nothing in a URI is signed.** The string `skill://<authority>/...` says only what the server claims. Any server that can return that listing can use any authority, including one that looks like a vendor's.
- **The authority is the same for every entry the server returns.** A malicious or compromised server can name its own content with a trusted-looking authority, and the client has no independent check.
- **The authority does not bind content to a key.** Digests bind bytes to a listing the server supplied, but they do not prove the listing came from the publisher. A digest in the same response as the content proves only self-consistency.
- **This fixture uses `eval.example`.** The `.example` TLD is reserved for documentation and testing (RFC 2606), so it is not a real publisher domain anyway.
- **Public caching makes a bad listing worse.** `ttlMs: 300000` and `cacheScope: "public"` mean a bad listing can be served to other clients for five minutes.

Publisher authentication needs something the server cannot forge by naming, such as a signature from a key the client already trusts, a trusted registry, or a transport identity the client verifies independently.

### Recommendations

1. Reject any skill whose frontmatter `name` differs from its directory segment.
2. Resolve each resource URI as follows: percent-decode unreserved characters, remove dot segments, then require the result to start with the skill directory plus a trailing `/`.
3. Reject encoded path separators and dots (`%2e`, `%2f`, `%5c`) in resource paths outright.
4. Do not treat the URI authority as a trust signal.

### Concrete values for checking

- Entry name: `byte-review`; directory segment: `wrong-name`
- Escaping resource: `skill://eval.example/wrong-name/%2e%2e/private.txt`
- Normalized target: `skill://eval.example/private.txt`
- Skill directory prefix that should contain it: `skill://eval.example/wrong-name/`
- Authority in both entries: `eval.example`
