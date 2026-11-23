# What a wiki export looks like and what it loses

Written from the vendors' public export help pages and the shapes of exports seen in practice. Not re-fetched while writing; check the pages below before telling a user exactly which menu items to click, because menus change.

- Notion export help: https://www.notion.com/help/export-your-content
- Confluence space export help: https://confluence.atlassian.com/doc/export-content-to-word-pdf-html-and-xml-139475.html
- GitHub wiki (a Git repository of Markdown files): https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis

## Notion, Markdown and CSV export

- Pages become `.md` files; nested pages become folders named like the parent page.
- Each file and folder name ends with a space and a 32-character hexadecimal id. The script strips that id when it needs a title from a file name.
- Links between pages are percent-encoded relative paths (spaces become `%20`), so they only resolve after decoding. The script decodes them.
- Page properties (owner, last edited time, tags) appear as lines at the top of the file in the Markdown export, for example `Owner: Name` and `Last edited time: March 3, 2026 10:00 AM`, or as a table in the HTML export. Both forms are recognised.
- A person property usually exports as a display name, not an account, so a person who left still shows as owner. Compare with a roster.
- Database rows export as pages plus a CSV; the CSV is not read.

## Confluence, HTML space export

- One `.html` file per page plus an `index.html` listing the pages; attachments sit in a separate folder.
- Page titles in the HTML title tag are prefixed with the space name and a colon; the script keeps only the part after the last " : ".
- A small metadata line near the top reads like "Created by Name, last modified on Mar 03, 2026". The modified date is read; the creator is not treated as the owner.
- Confluence has no built-in owner field on a page. Ownerless is the normal result unless the team puts an owner line or a page property in the content. Say this before presenting a large ownerless count as neglect.
- Page hierarchy (parent and child) is not folders; it lives in the index and breadcrumbs. Depth findings from folder paths understate the real tree.

## GitHub wiki or any Git-based Markdown wiki

- Flat folder of `.md` files; titles come from file names with hyphens for spaces.
- Links often use `[[Page Name]]`; the script matches those against file names, ignoring case and treating spaces, underscores and hyphens as the same.
- File modified times are the clone time, not the edit time. Use `git log` dates if the user can supply them, or accept `undated`.

## When dates are missing

Use the order: date written in the page, then the vendor's last-edited property, then file modified time. File time is only trustworthy for a folder copied without touching the files. The script reports when most undated pages share a single day.
