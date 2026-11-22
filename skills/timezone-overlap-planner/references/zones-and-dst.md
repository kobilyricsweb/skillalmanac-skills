# Zones, DST and weekends: lookup tables

## Contents

1. Abbreviations to refuse and what to ask
2. DST rule families and the gap weeks
3. Zones that surprise people
4. Weekend patterns to confirm
5. Naming traps in the tz database
6. Sources

Rules change by government decision. Treat every row below as a prompt to confirm with the user, and let the tz database (via the script) decide offsets. Weekend and holiday facts are never in the database: always take them from the user.

## 1. Abbreviations to refuse and what to ask

The script exits 2 for any zone without a slash (other than UTC). Ask for the city-based IANA name. Useful follow-up questions:

| Said | Could mean | Ask |
|---|---|---|
| IST | India, Israel, Ireland (summer) | "Which city?" Kolkata, Jerusalem or Dublin |
| CST | US Central, China, Cuba | Chicago, Shanghai or Havana |
| BST | British Summer Time, Bangladesh | London or Dhaka |
| EST / PST / MST | the winter name of a US zone, often used all year | New_York, Los_Angeles, Denver; Phoenix if no DST |
| AST, GST, SST | several regions each | the city |
| CET / EET | a whole family of countries | the city, since DST dates are shared but weekends are not |
| "Eastern", "Pacific" | a US or Canadian region | New_York / Toronto, Los_Angeles / Vancouver |
| "GMT" | London in winter only | London if they mean "UK time" |

A bare UTC offset (such as +05:30) is not a zone. Use it only as the fixed-offset fallback and say that DST is then not tracked.

## 2. DST rule families and the gap weeks

| Family | Starts | Ends |
|---|---|---|
| United States, Canada (most) | second Sunday of March, 02:00 local | first Sunday of November, 02:00 local |
| European Union and the United Kingdom | last Sunday of March, 01:00 UTC | last Sunday of October, 01:00 UTC |
| Israel | Friday before the last Sunday of March | last Sunday of October |
| Southern hemisphere (Australia southeast, New Zealand) | first Sunday of October (Australia), last Sunday of September (New Zealand) | first Sunday of April |
| No DST | India, China, Japan, Korea, Singapore, most of the Gulf, Arizona (not the Navajo area), Hawaii, most of Africa and Brazil | - |

The weeks that break recurring meetings:

- US and Europe: the US moves about three weeks before Europe in spring, and Europe moves about one week before the US in autumn. In those weeks a New York to London gap is 4 hours instead of 5, and Berlin is 5 hours instead of 6.
- Northern and southern pairs (London and Sydney): the gap changes twice a year by an hour, in two steps weeks apart, because both hemispheres switch.
- Two zones in the same family usually move together, so their gap does not change; the script reports only gaps that change (`relative_offset_shifts`).

## 3. Zones that surprise people

| Zone | Offset note |
|---|---|
| Asia/Kolkata | UTC+5:30, no DST |
| Asia/Kathmandu | UTC+5:45; use `step_minutes` 15 so slots can land on :45 |
| America/St_Johns (Newfoundland) | UTC-3:30 standard, DST like Canada |
| Australia/Adelaide | UTC+9:30 standard |
| Australia/Lord_Howe | 30-minute DST step |
| America/Phoenix | UTC-7 all year; in summer it matches Los Angeles, in winter Denver |
| America/Mexico_City | no DST since 2022 |
| America/Sao_Paulo | no DST since 2019 |
| Africa/Casablanca | clock paused during Ramadan; the database encodes it, so trust the script, not memory |
| Iran, Egypt, Jordan, Syria, Lebanon, Paraguay, Chile | rules changed in recent years; trust the installed database and say which tzdata version if a result looks odd |

## 4. Weekend patterns to confirm

Never assume Saturday and Sunday. Ask, and pass `days_off`.

| Place | Common pattern (confirm) |
|---|---|
| Most of the Americas, Europe, India, China, Japan | Saturday and Sunday |
| Israel | Friday (often short) and Saturday: use `["fri","sat"]`, or keep Friday and tell the user the working day is short |
| Egypt, Saudi Arabia, Kuwait, Qatar, Bahrain, Jordan | Friday and Saturday (changes happen) |
| United Arab Emirates | Saturday and Sunday for most employers, Friday short |
| Iran, Afghanistan | Friday, with Thursday often a half day |
| Shift workers and shops | any days: ask |

Public holidays: collect them as dates in each person's own country and pass them in that person's `holidays` list (or the shared `holidays` list for company-wide days). The script has no holiday data.

## 5. Naming traps in the tz database

- `Etc/GMT+5` means UTC minus 5 (the sign is deliberately inverted) and never has DST. The script warns.
- Old names still resolve: `Asia/Calcutta` is `Asia/Kolkata`, `Europe/Kiev` is `Europe/Kyiv`, `Asia/Katmandu` is `Asia/Kathmandu`. Prefer the new name in reports.
- "US/Eastern" style names exist but are links to city zones; prefer the city.
- Country-level zones do not exist: the United States has many zones, so ask for the city. Same for Russia, Canada, Brazil, Australia, Mexico, Indonesia.
- On Windows, Python has no zone data of its own. The PyPI package `tzdata` supplies it. The script never installs anything: ask the user to install `tzdata` in their own environment, or supply fixed offsets.

## 6. Sources

- IANA time zone database and its theory notes: https://www.iana.org/time-zones
- Python standard library `zoneinfo` (behaviour of ambiguous and missing local times, the tzdata fallback): https://docs.python.org/3/library/zoneinfo.html
- PyPI `tzdata` package page: https://pypi.org/project/tzdata/
