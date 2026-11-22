# Email signature builder

## One line

Turns a JSON file of contact fields into a table-based HTML email signature and a matching plain-text signature, with field checks and a text color contrast check.

## What it does

The skill runs a Python script that reads one JSON object with up to seven contact fields: name, title, company, phone, email, website, and text color. It checks each field against a fixed rule. A bad phone number, an email without a dotted domain, or a text color that is not six hex digits stops the run and names the field. The script then measures the text color against white using the WCAG 2.x contrast formula. A ratio below 4.5 to 1 stops the run with a finding and writes nothing, so a pale gray never reaches the user's signature. When every check passes, the script writes two new files: an HTML signature built from one table at 600 pixels maximum width with inline styles and no images, and a plain-text version with the same fields in the same order. The script never overwrites an existing file and never writes to the input path.

## When to use

Use it when a person or small team needs a signature that displays the same way in several mail clients, and the signature has to be text, not a graphic. It suits a one-off signature for a new hire, a shared template for a sales group that will paste it into different clients, or a check of phone and email values before a batch of signatures goes out.

## When not to use

Do not use it for signatures with logos, banners, social icons, or tracking images, since the skill ships no image handling. It does not send mail, install a signature into an account, or edit a signature already set in a mail client. Brand design choices beyond the text color are outside its scope.

## Requirements

Python 3.9 or later. Standard library only. No network access, no packages to install, and no subprocess calls. The input file must be UTF-8 JSON and at most 2 MB.

## Example

Command run from a scratch folder, with relative output names:

```
python -I "<skill-folder>/scripts/signature.py" "<skill-folder>/fixtures/valid.json" signature.html signature.txt
```

Result, stdout and exit 0:

```
{"status": "ok", "contrast_ratio": 12.63, "written": ["signature.html", "signature.txt"]}
```

Content of `signature.txt`:

```
Ada Lovelace
Analytical Engine Analyst
Example Analytical Co

T: +1 (555) 010-2030
E: ada@example.com
W: www.example.com
```

The same run with `fixtures/bad-phone.json` ends with exit 2 and this stderr line:

```
{"status": "error", "code": "BAD_FIELD", "message": "phone needs 7 to 15 digits and only digits, spaces, ( ) . - and a leading +", "field": "phone"}
```

## Limits

The contrast check covers only the text color against a white background. It does not check the link color, the background of a dark-mode client, or the font. The HTML is not tested in any mail client. Phone and email rules are format checks, not proof that a number rings or an address receives mail. Names with unusual scripts pass the length rule but are not checked for character set. The skill writes the signature for one person per run.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
