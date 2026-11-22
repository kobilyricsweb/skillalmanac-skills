# Naming audit rules and facts

## Contents

1. Platform facts the rules rest on
2. Date forms and how each is converted
3. Version tag and series rules
4. Character sets
5. Inference and thresholds
6. Plan and collision procedure

## 1. Platform facts the rules rest on

- Windows rejects `< > : " / \ | ? *` and control characters in names, rejects names ending in a space or a dot, and reserves the device names CON, PRN, AUX, NUL, COM1 to COM9 and LPT1 to LPT9, including when an extension follows. Many Windows tools still stop at 260 characters for a full path. Source: https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file
- Windows and default macOS volumes treat `Report.txt` and `report.txt` as one name; Linux and most web storage treat them as two. A folder that travels between them can silently merge or overwrite. Default macOS volumes also treat a precomposed accent and its decomposed form as the same name, which is why the script groups names by Unicode form as well as case.
- Sync clients add a long prefix (the local folder path) in front of every file path, so the audit adds `--prefix-len` to each path before comparing with `--max-path`. Check the current documented limit of the sync product in use, for example https://support.microsoft.com/en-us/office/restrictions-and-limitations-in-onedrive-and-sharepoint-64883a5d-228e-48f5-b3d2-eb39e07630fa
- Dates written year, month, day with zero padding sort in time order when names are sorted alphabetically; that is the only reason the convention prefers them. Standard: https://www.iso.org/iso-8601-date-and-time-format.html

## 2. Date forms and how each is converted

| Form seen | Example | Result |
|---|---|---|
| day, month name, year | `12Mar2026`, `12 March 2026` | `2026-03-12`, code `NON_SORTABLE_DATE` |
| month name, day, year | `March 12, 2026` | `2026-03-12` |
| year, month, day with `.` or `_` | `2026.03.12` | `2026-03-12`, code `NON_ISO_DATE` |
| numeric day-month-year, four-digit year | `14-03-2026` | first number above 12: day first; second above 12: month first; equal numbers: unambiguous; otherwise `AMBIGUOUS_DATE` unless `--date-order` is given |
| two-digit year | `03-04-26` | always `AMBIGUOUS_DATE` (with dots it is skipped as a probable version number) |
| compact against ISO | `20260312` | converted to the style the convention names, `NON_ISO_DATE` |
| impossible date | `31-02-2026` | left unchanged, `NON_SORTABLE_DATE`, decision |

`--date-order` resolves only the ambiguous case; a date that cannot be valid in the stated order (month 14) stays a decision. A date is moved to the front only when the convention starts with a date and the name holds exactly one.

## 3. Version tag and series rules

- Tag: `v`, `ver`, `rev` or `version`, optional separator, digits, at the end of the stem. The convention fixes the width through `{nn}`. Inferred width is the most common width in the tree, never below 2.
- Padding exists so that `v10` sorts after `v09`. A tag with more digits than the width is left alone.
- Series key: folder, extension and the stem before the tag with a leading date removed and case folded. Different extensions are different series, so `cover_v03.psd` and `cover_v03.png` are not duplicates.
- Latest means highest number. Gaps are listed only when the span is 50 or less. Two files with the same number in one series are `DUPLICATE_VERSION` and are never renamed by the plan.
- The `FINAL_STYLE` token test: after splitting on `-`, `_`, space and `.`, a token made of `final`, `latest`, `newest`, `real`, `actual`, `usethis` or `finished` (repeated or followed by digits, optionally after `v` and a number) is flagged. `new` and `old` alone are not flagged because they occur in real names.

## 4. Character sets

- Forbidden (portable core): `< > : " | ? * \ /` and control characters; replaced by a separator.
- Risky: `# % & { } $ ! ' ` @ + = ; , ^ ~ [ ] ( )`. Apostrophes and backticks are deleted, the rest become separators.
- Whitespace of any kind becomes `-` inside a field. Runs of `_` and `-` that contain an underscore collapse to `_` (field separator); other runs collapse to one `-`. A leading `_` or `.` is kept, since it is a deliberate sort or hidden marker.
- Folder names keep their case; only characters, spaces, trailing dots, reserved names, length and Unicode form are checked.

## 5. Inference and thresholds

| Value | Why |
|---|---|
| 50 percent of files | a date or version token is adopted into the inferred pattern only when at least half of the files carry it, so a few odd files do not define the convention |
| separator `_` | chosen when any file stem contains an underscore, else `-` |
| 200 characters (path), 100 (name) | house working values: headroom under the 260-character limit of many Windows tools, and names a person can still read in a file dialog |

An inferred convention is a proposal. Violations that depend on it (`NO_DATE`, `NO_VERSION`, `PATTERN_MISMATCH`, `DATE_POSITION`, `VERSION_FORMAT`) are only real defects after the user confirms the pattern.

## 6. Plan and collision procedure

1. Compute each folder's new name; hold back any folder rename that would match a sibling's name ignoring case and Unicode form.
2. Compute each file's new name; accept it only when the result has no remaining defect code and fits the pattern.
3. Group the final names per folder together with the final folder names; every renamed file whose new name equals another name in that group is held back, and the check repeats until stable.
4. Verify the whole end state: every file and folder path, compared ignoring case and Unicode form, must be unique among the paths the plan changed. Report `plan_is_collision_free`.
5. Existing collisions that the plan does not touch stay in `collisions[]` for the user; the plan never resolves them by choosing a winner.
