## Contents

- How note editors resolve links
- What breaks when a file moves
- Tags
- Frontmatter
- Sources

# Link, tag and frontmatter rules behind the findings

Read the section that matches the question. These are the behaviours the script mirrors, in our own words, drawn from the public help pages listed at the end.

## How note editors resolve links

- A wikilink `[[Note]]` names a note by file name without `.md`. Matching ignores case. Writing `[[folder/Note]]` adds a path, and a partial path such as `[[folder/Note]]` also matches `vault/area/folder/Note.md`.
- `[[Note|shown text]]` changes only what is displayed. `[[Note#Heading]]` and `[[Note#^block-id]]` point inside the note; the part after `#` is not part of the file name. `[[#Heading]]` links within the same note.
- `![[file]]` embeds a note or an attachment. An attachment is any non-Markdown file and keeps its extension in the link, for example `![[data.csv]]`.
- A name in the frontmatter `aliases` list also resolves to that note. The script treats an alias as a fallback when no file has that name.
- When two notes share a name, the editor resolves a name-only link to one of them by its own rule (the shortest path wins in the mainstream editor), and the other is easy to link to by mistake. The script reports this as ambiguous and counts both notes as linked.
- Links also appear in frontmatter properties as quoted wikilinks; the script reads them like body links.
- Ordinary Markdown links (brackets followed by a path in parentheses) resolve relative to the note holding them first, then from the vault root (the script tries both); spaces may be written as `%20`. Links starting with a scheme such as `https:` or `mailto:` are outside the vault and ignored.
- Links inside fenced code, inline code, `%%comments%%` and HTML comments are not links, and neither are `#words` in them. The script blanks those regions before scanning.

## What breaks when a file moves

- Name-only wikilinks survive a move to another folder, as long as the file name stays unique. This is why the plans never rename a file.
- Links written with a folder path, and ordinary Markdown links with a path, point at the old location. Many editors rewrite them automatically only when the move happens inside the editor and the "update internal links" option is on. A move made in a file manager, by a script or by `git mv` does not rewrite anything. That is the reason `path_links_affected` exists.
- Anything outside the vault that points into it by path (a published site, shortcuts, a sync rule, a plugin setting naming a folder) also breaks silently.
- Moving a note into a folder that a plugin treats specially (templates, daily notes, an excluded folder for search) can change how it behaves. Ask which folders are special before proposing destinations.

## Tags

- A tag is `#` followed by letters, digits, underscore, hyphen or slash, with at least one non-digit. `#2024` is not a tag; `#2024/q1` is. A `#` followed by a space is a heading marker, and a `#` glued to a word or a URL is not a tag.
- Slash makes a hierarchy: `#project/alpha` is a child of `#project`.
- Tags are case-insensitive in search, so `#Meeting` and `#meeting` are the same tag to the editor but look different on disk. That is why case variants are flagged: the display and some tools differ.
- In frontmatter the list is `tags`, written as a block list, as `[a, b]`, or as a comma or space separated string. The `#` is optional there.
- Renaming must replace whole tags. `#plan` is a prefix of `#planning` and of `#plan/q1`; a naive replace corrupts both.

## Frontmatter

- A block is valid only when the very first line of the file is `---` and a later line is `---` (or `...`). A file that begins with `---` and never closes is flagged `unclosed`, since it may be a horizontal rule or a damaged block.
- A byte-order mark at the start of the file is tolerated by the script and should be left alone.
- Adding a block to a note that has none is an edit to the note. Keep it minimal and never invent values.

## Sources

Public help pages, read for the behaviours above; check them again if an editor release changes behaviour:

- https://help.obsidian.md/links (internal links, aliases, embeds, link updating on rename)
- https://help.obsidian.md/tags (allowed tag characters, nested tags)
- https://help.obsidian.md/properties (frontmatter properties, tags and aliases fields)
