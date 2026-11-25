```csv
id,zip,phone,note
00731,02134,0501234567,=SUM(A1:A9)
00732,10001,0529876543,ok
00733,07030,0541112222,+1 call back
```

- **Leading zeros:** Double-clicking a CSV in Excel strips leading zeros from `id`, `zip` and `phone` (`00731` becomes `731`). Have your colleague use Data > From Text/CSV and set those three columns to Text, or they will lose the zeros.
- **Formula in `note`:** The first row's `note` is `=SUM(A1:A9)`. Excel will evaluate it as a formula and show a number, not the text. I left the value as it was in the source; if it should be literal text, it needs to be changed before import.
- **Source:** Converted from `t2.json` (3 records, 4 fields each). I did not write a file.
