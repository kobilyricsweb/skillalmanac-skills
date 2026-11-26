## Audit of `inputs/bad-paths.json`

**Verdict: reject this entry.** It has two defects: the SKILL.md URI does not match the frontmatter name, and a resource URI escapes the skill's own directory after percent-decoding. The `digest` fields were ignored, as you asked.

### Concrete values

| Field | Value |
|---|---|
| Frontmatter `name` | `byte-review` |
| SKILL.md URI | `skill://eval.example/wrong-name/SKILL.md` |
| Resource 1 | `skill://eval.example/wrong-name/SKILL.md` (size 111) |
| Resource 2 | `skill://eval.example/wrong-name/%2e%2e/private.txt` (size 7) |
| `ttlMs` / `cacheScope` | `300000` / `public` |

### Findings

1. **Name mismatch.** The frontmatter says `byte-review`, but the URI path segment is `wrong-name`. The supplied baseline `inputs/valid.json` uses `skill://eval.example/byte-review/SKILL.md` with the same frontmatter, and the supplied file `inputs/drift/byte-review/SKILL.md` also declares `name: byte-review`. The bad entry is the only one where the path segment and the name disagree. A client that keys skills by path would register this one under a name the file does not declare.

2. **Resource containment failure.** Resource 2 is `wrong-name/%2e%2e/private.txt`. Under RFC 3986, percent-encoded unreserved characters are normalized before comparison (§6.2.2.2), so `%2e%2e` becomes `..`. Dot-segment removal (§5.2.4) then gives:
   - `/wrong-name/%2e%2e/private.txt` → `/wrong-name/../private.txt` → `/private.txt`
   - Full resolved URI: `skill://eval.example/private.txt`, which is outside `skill://eval.example/wrong-name/`.

   A naive check that looks only for a literal `..` would miss this. The check has to run after percent-decoding and dot-segment normalization, and encoded dot segments should be rejected outright. The valid baseline's resource (`byte-review/references/notes.md`) stays under its skill root.

3. **Unverifiable resource.** `private.txt` is not among the supplied inputs, so I could not check its content or existence.

4. **Digest (not assessed).** The SKILL.md size of 111 matches the byte count of the supplied file, and the digest equals the baseline's. As instructed, I did not treat the digests as evidence either way.

### Why a server URI authority is not publisher authentication

The `eval.example` in `skill://eval.example/...` is a name the server writes into its own response. Nothing in the entry binds it to a party who controls that domain:

- **Self-asserted.** Any server can emit any authority. The authority says where the server claims the skill lives, not who wrote it.
- **No cryptographic binding.** The entry has no signature, certificate, or trusted key. Nothing ties the content to the authority.
- **Same trust channel.** The authority arrives in the same untrusted message as the content, so it cannot vouch for that content.
- **Cacheable.** `cacheScope: "public"` with a 300 s TTL means the response may be shared across clients, so the label carries no proof of origin for any one of them.
- **Ambiguous namespace.** Two servers can use the same authority, and a server can claim an authority it does not control.

Publisher authentication would need something like a signature verified against a trust root the client already holds, or an out-of-band trust decision. The authority can only be used as a namespace key.

### Limits

- I did not consult the public MCP Skills extension documentation. The findings rest on the supplied inputs and general URI rules (RFC 3986). If the extension spec has a specific containment or name-matching rule, I have not checked its wording.
- The "name must equal the directory" convention comes from common Agent Skills practice, not from anything I verified in the supplied files.
- I did not install or run any supplied skill. I only read the JSON and Markdown files.
