## Contents

1. Markdown outline
2. JSON outline
3. What is read from a .pptx

## 1. Markdown outline

One file, slides separated by a line holding only `---` (this is also what Marp and reveal.js use, so the same file can feed them). An optional front matter block at the top (`marp: true` and similar key lines) is ignored. Use `#` headings, not underlined ones, so the separator is never ambiguous. Lines inside code fences are kept as body.

```markdown
# Guest checkout cut abandonment by a third

Q3 review for the product board

Notes: Open with the result, then say what we ask the board to approve.

---

# Abandonment fell from 31% to 21% after the redesign

Chart: Bar chart, abandonment before (31%) and after (21%)
Source: Internal analytics, checkout funnel, Jan-Sep 2026

Notes: The one number to remember is ten points. ...

---

# Appendix: effort estimate

- Canada: 2 engineer-weeks
```

How each line is read:

| Line | Counted as |
|---|---|
| First `#`, `##` or `###` line | the headline |
| `Chart: description` | one chart. An image whose alt text or file name contains chart, graph or plot also counts as one chart |
| `Source: text` | the source for every chart on that slide; ignored as a body line |
| `![alt](file)` | an image; empty alt text is an `image-no-alt` error |
| `Notes: text` (also `Speaker notes:`) | start of the notes, which run to the end of the slide |
| An HTML comment (Marp style) | notes too; comments holding style directives such as a `_class` or `paginate` setting are ignored |
| Table rows | one body line each, separator rows ignored |
| Anything else non-empty | one body line |

A slide whose headline begins with "Appendix" starts the appendix; every later slide counts as appendix. A slide with no body, chart or image is treated as a divider.

## 2. JSON outline

A list of slide objects, or `{"slides": [...]}`.

```json
{"slides": [
  {"headline": "Tickets fell 40% after in-app help",
   "body": ["Pilot: 2,000 accounts"],
   "charts": [{"description": "Bar chart of tickets per 100 accounts", "source": "Support desk export, Mar-May 2026"}],
   "images": [{"alt": "Bar chart: control 12.5, pilot 7.5"}],
   "notes": "Say the result first ...",
   "appendix": false}
]}
```

`headline` (or `title`) and `notes` are strings; `body` is a string with one line per row or a list of strings; `charts` and `images` are lists of objects; `appendix` is optional and also starts the appendix. A wrong type stops the script with exit 2 and a message naming the slide.

## 3. What is read from a .pptx

| Item | Source in the file |
|---|---|
| Slide order | `ppt/presentation.xml` slide list, resolved through its relationships |
| Headline | the shape that is a title or centered-title placeholder |
| Body lines | every other non-empty paragraph in text shapes and tables, except slide number, footer and date placeholders and paragraphs starting with "Source:" |
| Notes | the body placeholder of the linked notes slide |
| Images | picture elements; the description is the alt text attribute |
| Charts | native chart frames, plus pictures whose alt text or name contains chart, graph or plot |
| Chart source | a paragraph starting "Source:" anywhere on the same slide |
| Font sizes | explicit run sizes only |

Files with a DOCTYPE or entity declaration in a part, parts over 20 MB, and decks over 500 slides are refused rather than parsed.
