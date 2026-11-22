# Detection rules in scripts/redact.py

Read this when a sample shows a false positive or a value was missed. Each rule says what it matches, how it is validated, and the known failure.

## Contents

- Validation checks
- Rules by category
- Known false positives and misses
- Sources

## Validation checks

- **Luhn (cards).** Take the digits from the right, double every second one, subtract 9 from any result above 9, sum everything; valid when the sum is divisible by 10. A random digit string passes about 1 time in 10, so a pass is evidence, not proof. The script also requires 13 to 19 digits, a first digit from 2 to 6 and at least two distinct digits.
- **Mod 97 (IBAN).** Move the first 4 characters to the end, turn letters into numbers (A = 10 through Z = 35), read the result as an integer; valid when the remainder after dividing by 97 is 1. Length must be 15 to 34 characters. A random string passes about 1 time in 97.
- **Candidate windows.** A card number may be written with single spaces or hyphens between groups. The script reads each run of digit groups and tests every window of up to 8 consecutive groups, so a date or an order number written next to a card does not hide it.

## Rules by category

| Category | Matches | Validation |
|---|---|---|
| PRIVATE_KEY | `-----BEGIN ... PRIVATE KEY-----` to the matching END line, or the BEGIN line alone if the block is cut off | none |
| API_KEY | `AKIA` or `ASIA` plus 16 upper-case letters or digits; `sk-` plus 20 or more of letters, digits, `_`, `-`; `gh` plus p, o, u, s or r, `_`, 36 or more alphanumerics; `xox` plus a, b, p, r or s, `-`; three base64url parts starting `eyJ` (JWT) | length only |
| URL_TOKEN | the value of a query parameter named token, access_token, refresh_token, id_token, api_key, apikey, key, secret, client_secret, password, passwd, pwd, pass, sig, signature, auth, authorization, session, sessionid, sid, jwt, code, an `x-amz-` credential or signature name, or ending `_token`, `_secret`, `_password`, `_apikey`; and the password in `https://user:password@host` | name match |
| CREDENTIAL | the value after `password`, `passwd`, `pwd`, `secret`, `client_secret`, `api_key`, `access_token`, `auth_token`, `token` followed by `:` or `=`; the value after `Bearer`; in JSON, any string whose key is one of those names | value 4 or more characters (Bearer 16 or more), not null, none, true, false |
| EMAIL | local part, `@`, dotted domain with a top-level label of 2 or more letters | pattern only |
| IBAN | two letters, two digits, then groups of up to 4 upper-case letters or digits, single spaces allowed | mod 97 and length; the longest valid reading is taken |
| CARD | see Luhn | Luhn, length, first digit |
| SSN | `NNN-NN-NNNN`, area not 000, 666 or 9xx, group not 00, serial not 0000 | pattern only |
| IPV6 | colon-separated hex groups | parsed by the standard library; `::1` and `::` are kept |
| IPV4 | four dot-separated numbers 0 to 255 without leading zeros | parsed by the standard library; 127.x, 0.0.0.0 and 255.255.255.255 are kept; with `--keep-private-ips` also 10/8, 172.16/12, 192.168/16 |
| PHONE | 9 to 15 digits, 2 to 6 digit groups. With a leading `+`: accepted. Without: 10 or more digits and parentheses, or all-space groups of 3 or more digits, or hyphens (at most 5 groups, at most 13 digits), or the dotted form `NNN.NNN.NNNN` | rejects dates (`2026-11-03`), dotted quads, year lists, anything followed by `:` |
| NAME, TERM | whole-word, case-insensitive match of an alias from your file; `|` joins aliases of one entry; spaces match any whitespace | alias length at least 3 |

Overlaps are resolved by the order above: the first category that claims a span keeps it. A key inside a URL stays a URL_TOKEN, and a name inside an email address is covered by the email.

## Known false positives and misses

- Version strings with four numbers that are each 0 to 255 (`1.2.3.4`, `10.0.19.45`) match IPv4. Three-number versions and numbers above 255 (`10.0.19045.3`) do not.
- Order, tracking or account numbers that happen to pass Luhn are redacted as cards.
- A 9 to 11 digit id written with spaces and groups of 3 or more digits can match PHONE.
- Local numbers without a prefix or with fewer than 10 digits (`555-0100`) are not detected.
- Phone numbers written as one unbroken digit run are not detected, because ids look identical.
- Non-US national id numbers (other than IBANs) are not detected.
- Secrets with no label and no known prefix are not detected.
- Anything not on your name list stays: the script has no name recognition.
- Percent-encoded or base64-wrapped values are not decoded, so an encoded email is not seen.

## Sources

- Luhn algorithm, described at https://en.wikipedia.org/wiki/Luhn_algorithm
- IBAN structure and the mod 97 check, described at https://en.wikipedia.org/wiki/International_Bank_Account_Number
- Access key id prefixes (`AKIA` long-term, `ASIA` temporary), described at https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
- US Social Security number area, group and serial exclusions, described at https://www.ssa.gov/employer/randomization.html
- Documentation address ranges used in the fixtures (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 and 2001:db8::/32), RFC 5737 and RFC 3849
