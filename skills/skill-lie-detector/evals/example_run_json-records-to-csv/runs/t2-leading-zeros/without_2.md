```csv
id,zip,phone,note
00731,02134,0501234567,=SUM(A1:A9)
00732,10001,0529876543,ok
00733,07030,0541112222,+1 call back
```

- **Leading zeros:** Excel strips them when it opens a CSV, so `00731` becomes `731` and `02134` becomes `2134`. To keep them, import via Data > From Text/CSV and set the `id`, `zip` and `phone` columns to Text. Double-clicking the file won't preserve them.
- **Formula risk:** `=SUM(A1:A9)` in `note` will be evaluated as a formula, not shown as text. `+1 call back` may also be read as a formula and show an error. Setting the `note` column to Text on import avoids both.
- **Source:** the input file is `t2.json` in the sandbox folder. I did not write a separate CSV file.
