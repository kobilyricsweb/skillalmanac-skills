## Contents

- Choosing a generator
- Known gaps to close by hand
- Source pages

## Choosing a generator

Pick the first row that matches the situation. Any of them can pass the contract; the inspector is the judge.

| Situation | Option | How it handles structure |
|---|---|---|
| Source is Markdown, plain structure, no strict brand | Pandoc (`pandoc in.md -o out.docx`) | Maps headings to Heading styles, YAML title and author to properties, `--toc` adds a contents field, `--number-sections` types numbers into headings. Styles come from a reference file: `--reference-doc=ref.docx`. Get the default one with `pandoc -o ref.docx --print-default-data-file reference.docx`, edit its styles in Word, reuse it |
| Python available, structure built in code | python-docx | `add_heading(text, level)` uses the Heading N styles (level 0 is Title), `add_table(rows, cols, style=...)`, `add_picture`, `core_properties.title` and `.author`. Start from the library's default template or a company template that already has Heading, Caption and a table style |
| JavaScript or TypeScript environment | docx (npm) | Declarative: paragraphs with heading levels, tables, images, headers and footers with a page-number element, a table-of-contents element, numbering configuration. Versions differ; confirm the option names for header rows and picture alt text in the installed version |
| The user's own template (.docx or .dotx) must be kept | python-docx on the template, or a template-fill library | Open the template, remove placeholder body, write content with the template's own style names. Check the style names exist before use |
| .NET or Java stack | Open XML SDK, docx4j | Full control of the XML; the most code for the same result |
| Only HTML or ODT exists | LibreOffice headless conversion to .docx | Style fidelity is the weakest of the options; run the inspector twice as often and expect heading styles to need checking |

Whatever is chosen, say which one in the report and keep the generation script next to the output so the file can be rebuilt.

## Known gaps to close by hand

These are the places generators commonly leave the contract unmet. Do not assume; run the inspector and see.

| Gap | What to do |
|---|---|
| Alt text not exposed by the API | Set the `descr` attribute on the picture's `wp:docPr` element after inserting it (in python-docx, through the inline shape's underlying XML element) |
| Repeating header row | Add a `w:tblHeader` element inside the first row's `w:trPr` |
| Caption style | Use the style named Caption (or Table Caption / Image Caption in some templates); the inspector also accepts text starting "Table N" or "Figure N" |
| Contents field is empty | Normal: the field is filled when Word updates fields. Tell the user; do not type a fake list |
| Heading numbering | Pandoc and many libraries type the numbers; a multilevel list is only present if the template has one linked to the heading styles |
| Core properties | Pandoc takes them from the YAML block; python-docx from `core_properties`; set them explicitly and let the inspector confirm |
| Table style | Library defaults often leave tables unstyled ("Normal Table"). Name the style in the call, and put it in `table_styles_allowed` |
| Page size | Libraries default to Letter or to the template's size; set it explicitly |
| Fonts | The font named in a style must exist on the reader's machine; otherwise Word substitutes silently. The inspector cannot see this |

## Source pages

Read in the authoring session from memory of their structure only; the pages were not fetched while writing this file, so confirm option names against the installed version.

- Pandoc manual, section on the docx writer and `--reference-doc`: https://pandoc.org/MANUAL.html
- python-docx documentation: https://python-docx.readthedocs.io/
- docx (npm) documentation: https://docx.js.org/
- Office Open XML WordprocessingML reference (element names such as `w:tblHeader`, `wp:docPr`): https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Open XML SDK: https://learn.microsoft.com/en-us/office/open-xml/open-xml-sdk
