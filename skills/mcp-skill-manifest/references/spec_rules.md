# Rules this skill applies, and where they come from

Read on 2026-11-26. The extension is in beta, so check the sources again before relying on a rule.

Sources:
- Spec: `specification/beta/skills.mdx` in github.com/modelcontextprotocol/ext-skills
- Schema: `schema/beta/schema.json` in the same repository
- Overview: modelcontextprotocol.io/extensions/skills/overview
- SEP-2640: modelcontextprotocol.io/seps/2640-skills-extension (historical; the spec wins where they differ)

Only the first 72% of the spec file and the first 41% of the schema file were read word for word. Rules marked (summary) come from a summary of the rest.

## Entry

| Rule | Source section |
|---|---|
| An entry has `uri`, `frontmatter` and `resources`; `_meta` is optional | Skill Entries; schema `Skill.required` |
| `uri` is the URI of the skill's SKILL.md | Skill Entries |
| Shape `skill://<skill-path>/<file-path>`; the skill root is the SKILL.md URI without `/SKILL.md` and without a trailing slash | Skill URIs |
| The last segment of the skill path MUST equal `frontmatter.name` | Skill URIs |
| The first segment SHOULD be a valid `reg-name`; a server MAY use another scheme | Skill URIs |
| Hosts MUST NOT resolve the authority over DNS or the network | Skill URIs |

## Frontmatter

| Rule | Source section |
|---|---|
| `frontmatter` is the SKILL.md YAML frontmatter as a JSON object, with every field the author wrote | Frontmatter |
| It MUST be identical in content to the frontmatter of the SKILL.md | Frontmatter |
| `name` and `description` are required strings | schema `Skill.frontmatter.required` |
| The name follows the Agent Skills naming rules | Names |
| Names SHOULD be unique within a server's listing | Names |

The spec text read does not say how YAML dates, key order or multi-line strings map to JSON. The script keeps dates as the text the author wrote.

## Resources

| Rule | Source section |
|---|---|
| `resources` is an array, or the string `"dynamic"`; anything else makes the entry invalid and hosts MUST NOT load it | Resources |
| The array lists every file of the skill exactly once, including the SKILL.md itself | Resources |
| Each `uri` MUST be the SKILL.md or a file within the skill's directory | Resources |
| `digest` is `sha256:` followed by 64 lowercase hexadecimal characters, over the file's raw bytes | Resources; schema `SkillResource` |
| `size` is the length in bytes of the same raw content | Resources |
| A nested skill's files are also listed by the enclosing skill | Resource Mapping |
| `"dynamic"` is for content generated so that stable digests cannot be published; hosts MAY decline it | Resources; Limits |

Ordering of the array, symlinks, hidden files, empty files and line endings are not addressed in the text read.

## Limits

| Rule | Source section |
|---|---|
| At most 512 resources per skill, SKILL.md included | Limits |
| At most 16 MiB (16,777,216 bytes) per skill, the sum of `size` | Limits |
| Servers SHOULD NOT serve a skill over either limit | Limits |

## Listing result

| Rule | Source section |
|---|---|
| `resultType` is `"complete"` | Listing Skills |
| `ttlMs` is an integer of 0 or more; `cacheScope` is `"private"` or `"public"`; both are required | schema `ListSkillsResult` |
| An entry is atomic and is never split across pages | Listing Skills |

## What a host does with it

| Rule | Source section |
|---|---|
| On a digest mismatch the host MUST NOT use the content | Integrity and Verification |
| A byte length that differs from `size` counts as a digest mismatch | Integrity and Verification |
| Reading a file that is not listed counts as a digest mismatch | Integrity and Verification |
| Frontmatter that differs field by field counts as a digest mismatch and the skill MUST NOT be loaded | Integrity and Verification |
| Hosts MUST NOT treat a digest match as a security boundary | Integrity and Verification |
| A stored approval is tied to the set of URIs and digests; a change revokes it | Overview; (summary) |
