# Listing page content: sensitive-data-redaction

**One line:** Replaces emails, phones, cards, IBANs, keys, IPs and listed names in a file with consistent placeholders before you share it.

## What it does

The skill gives an agent a seven-step procedure: state the purpose, choose categories from a decision table by document type, list the names and terms to hide, run a redaction script, review a report and the redacted file by eye, work only with the redacted copy, and optionally restore the real values in the answer. The script detects by content: a card number must pass the Luhn check and an IBAN the mod-97 check, so order numbers and random digits are mostly left alone. It writes a redacted copy and a report with counts and line numbers but never the values. The mapping from placeholders to originals is written only when asked, and only to a path the user chooses.

## Capabilities

- `scripts/redact.py redact`: writes `<stem>.redacted<ext>` and `<stem>.redaction_report.json`; text and log files are scanned line by line, `.json` files are parsed so the result stays valid JSON
- Categories: PRIVATE_KEY, API_KEY, URL_TOKEN, CREDENTIAL, EMAIL, IBAN, CARD, SSN, IPV6, IPV4, PHONE, plus NAME and TERM from lists you supply (aliases of one person share one placeholder)
- Options: `--keep-last4`, `--keep-private-ips`, `--skip`, `--dry-run`, `--mapping`
- `scripts/redact.py restore`: puts the originals back into an AI answer using the private mapping
- Warnings: mapping in the same folder as the shared output, input that already contains placeholder-like tokens, unreadable encodings
- A table of what the script cannot see (unlisted names, addresses, dates of birth, identifying combinations)

## When to use

You are about to paste a ticket, log, export or document into an AI tool or send it to someone, and you want emails, phone numbers, card and bank numbers, keys, IP addresses and named people replaced first, with a record of what was replaced.

## When not to use

Scanning a code repository for committed secrets (see coding-agent-guardrails and skill-safety-audit for code and agent safety), blocking agent actions, legal advice on privacy law, or producing data that is truly anonymous. The skill does not claim compliance with any regulation.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent replaces values by hand against the table and says the checksum validation was not run.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from the saved fixtures.

1. Command: `python scripts/redact.py redact evals/fixtures/support_ticket.txt --names evals/fixtures/names.txt --terms evals/fixtures/terms.txt --mapping private/ticket.mapping.private.json`. Result: 16 replacements (EMAIL 2 matches / 1 unique, PHONE 2, CARD 2 / 1, IBAN 1, SSN 1, IPV4 1, IPV6 1, NAME 3, TERM 1, URL_TOKEN 1, API_KEY 1). The order number `4111 1111 1111 1112` (fails Luhn), the timestamp `12:30:45` and the version `2.31.4` are left alone. Excerpt of the redacted file:

```
My name is [PERSON_1]. Please call me on [PHONE_1] or [PHONE_2].
I was charged twice on card [CARD_1] (the same card, [CARD_1], was used on 2026-11-02).
Refund to IBAN [IBAN_1] please. My account holder ID is [SSN_1].
Payment portal link: https://pay.example.test/checkout?order=48213&token=[URL_TOKEN_1]&lang=en
```

2. Command: `python scripts/redact.py redact evals/fixtures/server.log`. Result: 12 replacements; a private key block, an AWS-style key, three credentials (`password=`, `api_key=`, `Bearer`), an IPv6 address and three distinct IPv4 addresses; `::1`, `127.0.0.1` and the build number `10.0.19045` stay.

## Limits

- Free-text names are only found when listed; there is no name recognition.
- Phone, IPv4 and card detection are heuristics with known false positives and misses.
- Redaction is not anonymization and is not a compliance control.
- Text pasted into the chat has already reached the model; the skill protects later sharing.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 11 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A support export with a card number and a customer name; the user asks to share it with an AI tool.
2. The agent writes a names file, runs a dry run, then the real run; the report shows counts per category and no values.
3. The agent reads the redacted file, flags an unlisted nickname and a street address left for a hand edit.
4. The AI answer comes back with `[PERSON_1]`; a restore run puts the real name back into a separate file.

## FAQ seeds

- Does it need network access? No.
- Does the script ever print the sensitive values? No: the report has counts, locations and redacted context only. The optional mapping file does hold them.
- Is the result anonymous or GDPR compliant? No claim is made; redaction only removes what is detected or listed.
- Does it find names? Only names you list, with aliases on one line.
- How is it different from coding-agent-guardrails or skill-safety-audit? Those protect code, agent actions and skills; this redacts ordinary documents and logs before they leave your machine.
- Can I undo it? Yes, if you wrote a mapping file; keep it away from anything you share.
- How do I uninstall? Delete the skill folder; created `.redacted` files and mappings are yours to delete.

## Changelog

- 0.1.0, 2026-11-21: first draft, not re-verified beyond static lint and script fixtures.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5) under editorial direction; the accountable editor is Global Media Holdings. No human review has taken place yet.
