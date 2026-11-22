# rows-to-html-table

## One line

Converts a CSV file or a JSON array of objects into one escaped HTML table fragment with a caption, scoped column headers, and a row and column count.

## What it does

The skill runs one Python script, `scripts/rows_to_html.py`, against a file you name. A CSV file is read with its first row as the column header. A JSON file must hold an array of objects; nested objects are flattened into dot-separated column names such as `buyer.name`, and arrays are flattened by index such as `lines.0.sku`. Each cell is HTML-escaped, so an ampersand, a less-than sign, or a quotation mark in the source comes out as text and never as markup. The header cells carry `scope="col"`, and the rows sit in a `tbody` below a `thead`. The caption is required, which keeps every table labeled for screen readers.

The script writes to a new file only. If the output path already exists it stops with exit code 2 and changes nothing. It prints a one-line JSON summary with the row count, the column count, the names of any numeric columns, the list of ragged rows, and the output size in bytes. A ragged row is a CSV row whose cell count differs from the header, or a JSON object whose keys are not the full set of keys seen across the file. Ragged rows are still written, with blank cells where a value is missing, and the exit code becomes 1 so the agent can flag them for review.

The skill also gives the agent a fixed checklist: confirm the intake facts, run the command, map the exit code to a status word, count the table elements in the output file, and hand back a status block.

## When to use

Use it when a page needs a static table and the source is a CSV export or a JSON list of records, for example the saved result of a SQL query. It fits a one-off table for a help article, a comparison page, or a data appendix where the rows will not change between page builds.

## When not to use

Do not use it for spreadsheets in `.xlsx` form, for charts, for live tables that read from a database, or for front-end component code in React or another framework. It does not write CSS, so the numeric right-alignment depends on the page defining a `num` class. It does not sort, page, filter, or add a full HTML document around the table.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls, and no installed packages. The input must be UTF-8 text no larger than 2 MB. The caller must supply a caption and a new output path.

## Example

Command run on `fixtures/sample.csv`, which has five data rows and four columns, with `--align-numeric`:

```
python -I scripts/rows_to_html.py fixtures/sample.csv --output sample-table.html --caption "Sample parts" --align-numeric
```

Summary line on stdout, exit code 0:

```
{"rows": 5, "columns": 4, "numeric_columns": ["qty", "price"], "ragged_rows": [], "output_bytes": 992}
```

Written file:

```html
<table>
  <caption>Sample parts</caption>
  <thead>
    <tr>
      <th scope="col">item</th>
      <th scope="col">description</th>
      <th scope="col">qty</th>
      <th scope="col">price</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Widget A</td>
      <td>Fits &lt;small&gt; &amp; &lt;large&gt; frames</td>
      <td class="num">12</td>
      <td class="num">3.50</td>
    </tr>
    <tr>
      <td>Gadget &amp; Co</td>
      <td>Use with &quot;quotes&quot; only</td>
      <td class="num">7</td>
      <td class="num">10</td>
    </tr>
    <tr>
      <td>Bolt &lt;M6&gt;</td>
      <td>Steel &amp; zinc plated</td>
      <td class="num">250</td>
      <td class="num">0.12</td>
    </tr>
    <tr>
      <td>Panel</td>
      <td>Plain text row</td>
      <td class="num">3</td>
      <td class="num">199.99</td>
    </tr>
    <tr>
      <td>Cable</td>
      <td>Line one, with comma</td>
      <td class="num">40</td>
      <td class="num">1.5</td>
    </tr>
  </tbody>
</table>
```

The `<td` count is 20, which equals 5 rows times 4 columns, so the output passes the step 6 check in the skill.

## Limits

- It does not check whether the caption is accurate, whether the data is correct, or whether the table meets a particular accessibility standard. It adds caption, `scope`, and `thead` structure only.
- It does not test visual layout, colors, or the page CSS that the `num` class depends on.
- JSON keys that collide after flattening, for example a literal key `a.b` next to a nested `a` with key `b`, are merged without a warning.
- Numbers are written as the parser returns them. A large JSON float can appear in exponent form, and a number with a thousands separator is not treated as numeric.
- Only the comma delimiter is supported for CSV. There is no dialect detection, no quoting option, and no header-less mode.
- Duplicate column names and blank column names stop the run with exit code 2.
- The script does not sanitize links, does not add `rel` attributes, and does not check the output for deliverability or security beyond escaping cell text.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
