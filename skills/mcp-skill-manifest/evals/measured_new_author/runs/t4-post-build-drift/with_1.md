**Verdict: `inputs/valid.json` is not ready for publication.** It matches the SKILL.md but is stale for `notes.md` and is missing `new.txt`. A rebuilt manifest from `inputs/drift` passes `check --root`, and that is the file to publish once you confirm it.

**Discrepancies (saved manifest vs. `inputs/drift/byte-review`)**

1. **`references/notes.md` changed after the build.**
   - Saved: `size` 10, `sha256:216a1ef9acc7aa65e2f413bb753247a873ff4ae35400f6d66a39583d3acceb3a`
   - Current: 21 bytes, `sha256:20e504c3c6a99622cbc423a6f438a275a5361dd86ffa9eee2ed4ecc382d6db85`, content `Changed after freeze` plus a newline.
   - `check --root` reports "size is 21 bytes on disk, manifest says 10". The digest also differs, so a host would reject the file under the digest-mismatch rule. I can't tell from the inputs whether this edit was meant to happen after the freeze, so please confirm that.

2. **`new.txt` is not listed.**
   - Current: `skill://eval.example/byte-review/new.txt`, 20 bytes, `sha256:dde888f1ed4b631be5a2fcaad2bd50c894606b7d5332d91e05b609fca9bc5f1d`, content `new supporting file` plus a newline.
   - `check --root` reports "file exists but is not listed". Under the spec rules a host treats reading an unlisted file as a verification failure. Since you named the drift folder as the authoritative set to serve, this file should be listed.

**Unchanged:** `SKILL.md` (111 bytes, `sha256:1c17f105c01d22c755ced5dfb527aa5029670bc96358fd4a9d642020bbd8079a`), the frontmatter (`name: byte-review`, the description), the authority `eval.example`, the URI shape, `ttlMs` 300000 and `cacheScope` `public`. The saved manifest passes the structural check with no `--root`.

**Rebuilt manifest**

I built it with `build inputs/drift --authority=eval.example`. It is at `<local path>`. It has 1 skill, 3 resources and 152 bytes (111 + 20 + 21), with no errors or warnings. `check --root=inputs/drift` passes. Its resource order is SKILL.md, `new.txt`, `references/notes.md`, which is sorted path order. The spec text I read doesn't address ordering.

**Caveats**
- This is a beta extension, and the digests show only that the bytes match the list, not that the skill is safe or trusted.
- Any host that approved the earlier digests will need to re-approve, because approval is tied to the URI and digest set.
- The server still has to declare the extension and `resources` capabilities, answer `skills/list`, `skills/get` and `resources/read` with these exact URIs and bytes, and handle paging. The listing's `ttlMs` and `cacheScope` are freshness hints only.
- I made no source edits. I ran only the manifest skill's own `build` and `check` script, and did not install or execute any supplied skill. The rules come from `references/spec_rules.md`, which was read on 2026-11-26. I did not browse the public spec.
