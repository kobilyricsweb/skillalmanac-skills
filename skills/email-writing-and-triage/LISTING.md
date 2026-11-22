# Listing page content: email-writing-and-triage

**One line:** Triages an exported inbox with deadline and phishing flags, then drafts replies that never send and never invent figures.

## What it does

The agent runs a script over a JSON or mbox export. Each message gets one of seven categories by documented rules (suspicious, automated, fyi, urgent_reply, reply, waiting_on_them, sent), plus flags for deadlines, overdue dates, money keywords, reply-all risk and stale follow-ups. The script prints a strict JSON table and a work queue, and a second command validates a saved table. The agent then drafts replies by intent (decline, delay, ask, confirm, follow-up) from templates with a hard rule: any date, amount or promise must come from the thread or from the user's chat, otherwise it becomes a visible `[[NEEDS FROM YOU: ...]]` slot. Drafts go to the sender only. Nothing is sent and no network is used.

## Capabilities

- `triage` command: JSON triage table with category, reply_action, flags, reasons and resolved deadlines per message, a ranked `queue` and a `quarantine` list; message bodies are not copied into it
- `check` command: validates a saved table against the contract
- Deadline detection with cue words and date resolution against each message's own date (weekdays, "next Friday", "by EOD tomorrow", "within 3 business days", "5th of December")
- A never list, an intent table, tone limits with numbers, templates, a daily procedure and a fixed morning report

## When to use

You say triage my inbox, clear my email, what needs an answer today, draft a reply, say no politely, which mails have a deadline, or you paste an email and want an answer drafted.

## When not to use

Sending mail or connecting to a live mailbox, marketing and cold outreach, support-desk macros, legal or contract wording, translating or restyling a text.

**How it differs from `customer-support-replies`:** that skill answers a customer queue in the company's voice. This one sorts a personal or work inbox and drafts replies in the user's own voice, with a recipient-privacy and no-invented-figures rule set. Use that skill for helpdesk tickets and this one for an executive or professional inbox.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the rules in `references/triage-rules.md` by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of `python scripts/triage_mailbox.py triage evals/fixtures/mailbox.json --me dana@northwind.example --today 2026-11-17` (15 messages):

```
counts_by_category: suspicious 2, automated 2, urgent_reply 3, reply 3, fyi 3, waiting_on_them 1, sent 1
queue:      invoice-question, numbers-eod, contract-signoff, signed-form, board-prep, undated-file, pricing-ask
quarantine: it-phish, gift-cards
```

One row from the same run: message `contract-signoff` ("can you sign off by Thursday?", sent Monday 2026-11-16) is `urgent_reply`, `reply_action: draft`, reasons `question_mark` and `deadline_within_2_days`, deadline `Thursday` of kind weekday resolved to `2026-11-19` with `days_left` 2.

A second run on `evals/fixtures/mailbox.mbox` (4 messages, no `--today`) takes the reference date 2026-11-18 from the newest message, decodes the encoded subject "Café menu review", ignores a deadline that appears only in quoted history, and marks the mailer-daemon bounce `automated`.

No reply draft from a with-skill agent run is saved yet, so none is shown. The worked draft in `references/reply-templates.md` section 7 is written by hand, not from a run.

## Limits

- English wording only for request, deadline and phishing patterns.
- Thresholds are working values, not measured optima.
- The script cannot judge tone or open attachments and links.
- Quoted history in unusual client formats can leave old text in and add false deadlines.
- Categories order the day; a person decides what to send.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 7 script fixture cases pass. Not tested: efficacy against a baseline, trigger behaviour in any tool, native discovery, cross-tool installs, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run. Planned beats:

1. Drop a 15-message export into the chat; run `triage`; the table shows 2 quarantined, 3 urgent.
2. The agent reads the quarantine reasons and refuses to draft replies to them.
3. It drafts the top urgent reply with a `[[NEEDS FROM YOU: reply date]]` slot instead of a guessed date.
4. The morning report ends with a "Not checked" line.

## FAQ seeds

- Does it send my emails? No. It has no network access and only writes drafts for you to send.
- Does it need access to my mailbox? No, only an export file you choose to share.
- Will it promise prices or dates for me? No; figures not in the thread or your message become visible slots.
- Will a reply expose who else was on the thread? Drafts go to the sender only and name nobody from Cc or Bcc.
- Does it work with Outlook or Gmail exports? JSON as described in the script docstring and mbox-like text are read; other formats need converting first.
- How is it different from a plain "draft a reply" prompt? It adds a script-based triage with deadline detection, a never list, and a grounding line for every figure. No comparison run has been done yet.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
