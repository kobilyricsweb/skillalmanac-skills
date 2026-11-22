## Contents

- How to use this file
- Consent basis decision table
- Basics by region (orientation only)
- Footer and header checklist
- Sources

## How to use this file

These are orientation notes in the skill author's own words, read on 2026-11-21 from the sources listed at the end. They are not legal advice. In every plan note that touches consent, write "verify with counsel" next to the basis chosen. Rules change; check the source pages before relying on a number.

## Consent basis decision table

| How the person joined | `consent_basis` | Notes |
|---|---|---|
| Ticked an unticked box or typed their address into a form that says what they will get, and confirmed by link | `double_opt_in` | Strongest record; keep timestamp, source page, wording shown |
| Same form without the confirmation click | `express_consent` | Keep the same record; weaker against typo or mischief signups |
| Bought from the sender, and the emails promote similar products, and an opt-out was offered at collection and in each email | `existing_customer` | The "soft opt-in" idea in UK/EU rules and an "existing relationship" concept elsewhere; conditions differ, verify |
| No consent but a business reason (mostly B2B outreach) | `legitimate_interest` | EU/UK: needs a written balancing test and an easy objection route; not available for consumers in many member states for email marketing; verify |
| List bought, rented, scraped, appended, or a pile of business cards | none | Do not send. Offer a signup route instead |

## Basics by region (orientation only)

United States (CAN-SPAM): applies to commercial email, including B2B. Header and From information must be accurate; the subject must not mislead about the content; a clear opt-out must be in each message; opt-outs must be honoured within 10 business days; the opt-out must work for at least 30 days after sending and must not cost money or require more than a reply or a web page; the message must carry a valid physical postal address; ads should be identifiable as ads. Consent before sending is not required by this law, but opt-outs must be honoured, and several state laws add rules.

European Union (GDPR with the ePrivacy rules): marketing email to individuals normally needs prior consent that is freely given, specific, informed and unambiguous, as easy to withdraw as to give; the data subject has an unconditional right to object to direct marketing, and it must be honoured once raised. Sending to a bought list fails the "informed" and "specific" tests.

United Kingdom (UK GDPR with PECR): similar to the EU, with a soft opt-in for existing customers (similar products and services, opt-out offered at collection and in every message). Rules for emails to company addresses differ from those for individuals and sole traders.

Canada (CASL): needs express or implied consent before sending a commercial message; every message identifies the sender and carries a working unsubscribe processed within 10 business days; the sender must be able to prove consent.

Anywhere else: ask the user to name the countries of the recipients and tell them a local check is needed.

## Footer and header checklist

- Sender name and a monitored From address that match the brand the person signed up with
- Physical postal address in the footer
- Visible unsubscribe link that works without logging in and without extra steps, placed where it is easy to find
- `List-Unsubscribe` and `List-Unsubscribe-Post` headers for one-click unsubscribe where the platform supports them (RFC 8058)
- A line telling the person why they get the email ("You are receiving this because you downloaded the packing checklist")
- Unsubscribe processed immediately by the tool; the legal windows above are maximums, not targets

## Sources

- FTC CAN-SPAM compliance guide for business: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- GDPR Article 7 (conditions for consent) and Article 21 (right to object): https://gdpr-info.eu/art-7-gdpr/ and https://gdpr-info.eu/art-21-gdpr/
- UK ICO guidance on direct marketing and electronic communications: https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/
- Canada CASL guidance from the CRTC: https://crtc.gc.ca/eng/com500/guide.htm
- RFC 8058, one-click unsubscribe signalling: https://www.rfc-editor.org/rfc/rfc8058
