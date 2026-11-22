## Contents

1. Choosing a generator
2. python-pptx
3. Marp
4. reveal.js
5. Before you generate

Facts here are written from the authors' knowledge of the tools and were not re-fetched when this skill was written; confirm anything version-sensitive against the linked documentation. None of these tools is installed or run by this skill.

## 1. Choosing a generator

| Need | Use | Output |
|---|---|---|
| Editable .pptx that colleagues will change in PowerPoint, native charts, an existing template | python-pptx | .pptx with real text boxes and charts |
| Fast deck from the Markdown outline, PDF or slides that need not be edited by hand | Marp | PDF, HTML, or .pptx |
| A talk delivered in a browser, with speaker view, code samples or animation | reveal.js | HTML (PDF by print) |
| The user's tool is Google Slides or Keynote | build the .pptx, import it there, or give the validated outline | outline or .pptx |

If the user has a template, use it with python-pptx; a template's layouts, fonts and colours beat anything generated from scratch.

## 2. python-pptx

Python library for reading and writing .pptx files. Install command, to be run only after the user agrees: `python -m pip install python-pptx==<pinned version the user approves>`. Check first with `python -c "import pptx; print(pptx.__version__)"`.

What it covers: opening a template (`Presentation("template.pptx")`) or a blank deck; choosing a slide layout; filling title and body placeholders; adding text boxes, pictures with `add_picture`, tables and native charts with `chart_data` objects; writing speaker notes through the slide's notes text frame; saving. What it does not do: render slides, so it cannot show overflow, and it does not auto-fit text reliably, so keep text within the contract limits. Set alt text for pictures by editing the picture's non-visual properties `descr` attribute through its XML element, since the library has no dedicated setter for it. Documentation: https://python-pptx.readthedocs.io

## 3. Marp

Markdown slide framework; the command line tool is Marp CLI. The outline in `references/outline-format.md` is already valid Marp input once `marp: true` front matter is added at the top. Slides split on `---`; HTML comments become presenter notes, and per-slide directives (for example a class name such as `lead`) are also written inside an HTML comment, with an underscore before the directive name.

Typical commands (run only with the user's approval, since `npx` downloads the tool): `npx @marp-team/marp-cli@<pinned version> deck.md --pdf` and `... --pptx`. The standard .pptx export puts each slide in as an image, so text is not editable in PowerPoint; an experimental editable export exists and needs LibreOffice. State this to the user before choosing Marp for a deck that will be edited. Documentation: https://marpit.marp.app and https://github.com/marp-team/marp-cli

## 4. reveal.js

HTML presentation framework. A Markdown section in a reveal.js page separates slides with a line of `---` (and vertical slides with `--`) by default; a line starting `Note:` begins speaker notes; pressing S in the browser opens the speaker view with notes and timer; adding `?print-pdf` to the URL and printing from the browser produces a PDF. Needs the framework files, loaded from a package or a copy kept next to the deck. Documentation: https://revealjs.com/markdown/

## 5. Before you generate

1. The outline passed `scripts/deck_check.py` with `"ok": true`.
2. The generator is present (see the checks in step 7 of SKILL.md) or the user approved the install command.
3. Fonts used exist on the presenting machine, or are embedded, or fall back to two safe families.
4. After generating a .pptx, run `scripts/deck_check.py` on it, then render and look at every slide if a renderer is available. A generator can silently overflow text or lose notes.
