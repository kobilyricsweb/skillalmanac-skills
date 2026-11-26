## Audit of `inputs/bad-paths.json`

**Verdict:** The manifest fails. It has two errors: the frontmatter name doesn't match the URI, and one resource escapes the skill directory through `%2e%2e`. I did not install or execute any supplied skill. I ran only the skill's own `check` script in structure-only mode (no `--root`, no network), which reads the JSON file.

### Findings

**1. Name mismatch (error).** The spec rule is that the last segment of the skill path must equal `frontmatter.name`.
- `frontmatter.name` = `"byte-review"`
- URI last segment = `wrong-name` (in `skill://eval.example/wrong-name/SKILL.md`)
- The script's error: `the last segment of the skill path must equal frontmatter.name ('byte-review')`

**2. Resource escapes the skill root (error).** The second resource is `skill://eval.example/wrong-name/%2e%2e/private.txt`.
- Percent-decoding `%2e%2e` gives `..`, so the URI is `skill://eval.example/wrong-name/../private.txt`.
- Resolving that `..` moves the path to `skill://eval.example/private.txt`, which is outside the skill root `skill://eval.example/wrong-name`. The rule says each resource MUST be the SKILL.md or a file within the skill's directory.
- The script's error: `resource 'skill://eval.example/wrong-name/%2e%2e/private.txt' has an empty, . or .. path segment`.
- The encoding is the risk. A host that normalizes before decoding would see a literal `%2e%2e` segment, while one that decodes first would see `..`. The manifest should not depend on that difference, so it should be rejected outright, as the script does. The file is also a sibling of the skill, not part of it, so it should not be listed at all.

**Checks that passed (structure only):**
- `resultType` = `"complete"`, `ttlMs` = `300000`, `cacheScope` = `"public"`.
- The SKILL.md URI ends in `/SKILL.md`, has a scheme and authority, and the SKILL.md itself is listed in `resources` (first entry, size 111).
- Digests are ignored as you asked. Only their format was checked. I did not compare them to any bytes, since no skill files were supplied.

### Why the URI authority is not publisher authentication

- In `skill://eval.example/...`, `eval.example` is a naming namespace. The rules read say hosts MUST NOT resolve it over DNS or the network, so the host cannot check it against any real domain.
- The authority is a string the manifest's author writes. It is in the same response as the digests, so nothing binds it to a key, a certificate or a verified publisher. Anyone who can make a server can claim any authority, including another vendor's.
- Digests have the same limit. They are computed by the party that built the manifest and listed in the same response, so a match only shows the bytes match that listing. The rules say a digest match MUST NOT be treated as a security boundary.
- The rules I read define no publisher-authentication mechanism. Authenticity would need a separate control, such as a signature or a host-side trust policy for the server. I did not check the public spec for one.

### Suggested fixes (rebuild, don't hand-edit)

- Decide the intended name, then rename the folder and frontmatter to match. The fix belongs in the files, and the manifest should be rebuilt from them.
- Remove the `private.txt` resource. A file outside the skill's directory should not be served.
- Run `check --root` against the folder before publishing.

### Report

```
Manifest: inputs/bad-paths.json   Extension: io.modelcontextprotocol/skills (beta)   Built: not built (audit of a supplied file)
Skills: 1   Files: 2 listed   Bytes: 118 (111 + 7, from listed sizes)
Errors fixed: none (audit only)
Errors found:
  - name mismatch: URI segment "wrong-name" != frontmatter.name "byte-review"
  - escape: skill://eval.example/wrong-name/%2e%2e/private.txt decodes to ../private.txt, resolves to skill://eval.example/private.txt
Warnings and decisions: none
Excluded patterns: none
Check against folder: not run (no skill files supplied); structure check failed with 2 errors
Left for the server: capabilities, skills/get, resources/read, paging, dynamic skills
```

**Sources:** the supplied `inputs/bad-paths.json`, the skill's `SKILL.md`, `references/spec_rules.md`, and `scripts/skill_manifest.py`. I did not fetch any public MCP documentation. The spec rules were read in a previous pass and are only partly verified (the rules file says so itself).
