# FAQ Page Builder

## One line

Turns a pasted list of support questions with counts, plus your own facts, into a grouped FAQ page and a matching FAQPage JSON-LD block.

## What it does

The skill takes two inputs: question lines, each with the number of times customers asked it, and fact lines that you supply. It merges questions that are the same after light normalization, sorts them into four to six intent groups, and orders each group by how often the question was asked. Each answer is 60 words or fewer and draws only on the facts you supplied. Each number in an answer must appear in the fact it cites. A question that no fact covers is listed as TO-CONFIRM, with the fact you still need, instead of receiving a guessed answer. The JSON-LD block contains only answered questions and repeats their text exactly, so the markup never describes content that is not on the page.

## When to use

Use it when a support inbox or chat log has produced a list of real questions and someone must turn it into a page that a reader can scan. It fits a small help center, a product page with a questions section, or a support chatbot whose answers need to match a published FAQ. The counts you provide decide the order, so the most common questions appear first.

## When not to use

Do not use it to write policies, prices, delivery times, or legal and tax answers that your facts do not already state. It does not look up any individual customer's order, account, or charge. It is not a marketing copy tool, and it does not generate schema for pages other than FAQs. If your question list has more than 60 lines, split it into batches first.

## Requirements

A text-capable agent is enough. There is no network access, no script, and no file input. You provide the question lines in the form `<count> | <question>` and the fact lines in the form `F<n> | <fact>`. If you give no fact IDs, the agent numbers them in order.

## Example

The example below is a complete run on 12 pasted question lines and 10 supplied facts. The facts are a fictional store's shipping, return, payment, and warranty rules. Ten merged questions come from the 12 lines, two lines merged into existing questions, and one question stayed TO-CONFIRM because no fact covered international shipping.

## 1. Status

| Key | Value |
|---|---|
| Status | PARTIAL |
| Raw questions | 12 |
| Merged questions | 10 |
| Groups | 4 |
| Answered | 9 |
| TO-CONFIRM | 1 |
| Total count | 631 |

## 2. Page

### Shipping and delivery

#### How long does shipping take?

Orders ship within 2 business days after payment. Standard shipping takes 5 to 7 business days within the continental United States.

#### When will my order ship?

Orders ship within 2 business days after payment. You will receive a tracking number by email when your order ships.

### Returns, refunds and warranty

#### What is your return policy?

You may return an unused item within 30 days of delivery if it is in its original packaging. Refunds go to your original payment method after we receive and inspect the return.

#### Do your products have a warranty?

All products carry a 1-year limited warranty against manufacturing defects.

#### How do I get my money back after a return?

Refunds go to your original payment method after we receive and inspect your returned item.

### Orders and changes

#### Can I cancel my order?

Orders can be canceled before they ship.

#### Can I change my shipping address?

Yes, but only before the order ships. Contact support to request the change.

### Payments and gift cards

#### Do you take PayPal?

Yes. We accept Visa, Mastercard, and PayPal.

#### Can I use a gift card to get cash?

No. Gift cards cannot be redeemed for cash.

## 3. JSON-LD

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How long does shipping take?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orders ship within 2 business days after payment. Standard shipping takes 5 to 7 business days within the continental United States."
      }
    },
    {
      "@type": "Question",
      "name": "When will my order ship?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orders ship within 2 business days after payment. You will receive a tracking number by email when your order ships."
      }
    },
    {
      "@type": "Question",
      "name": "What is your return policy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "You may return an unused item within 30 days of delivery if it is in its original packaging. Refunds go to your original payment method after we receive and inspect the return."
      }
    },
    {
      "@type": "Question",
      "name": "Do your products have a warranty?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "All products carry a 1-year limited warranty against manufacturing defects."
      }
    },
    {
      "@type": "Question",
      "name": "How do I get my money back after a return?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Refunds go to your original payment method after we receive and inspect your returned item."
      }
    },
    {
      "@type": "Question",
      "name": "Can I cancel my order?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Orders can be canceled before they ship."
      }
    },
    {
      "@type": "Question",
      "name": "Can I change my shipping address?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, but only before the order ships. Contact support to request the change."
      }
    },
    {
      "@type": "Question",
      "name": "Do you take PayPal?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. We accept Visa, Mastercard, and PayPal."
      }
    },
    {
      "@type": "Question",
      "name": "Can I use a gift card to get cash?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No. Gift cards cannot be redeemed for cash."
      }
    }
  ]
}
```

## 4. TO-CONFIRM

| # | Question | Count | Missing fact |
|---|---|---|---|
| 1 | Do you ship internationally? | 26 | Whether international shipping is offered, and where and how long it takes. |

## 5. Merge and fact log

### Merges

| Merged question | Source lines | Total count | Facts cited |
|---|---|---|---|
| How long does shipping take? | 1, 2 | 162 | F1, F2 |
| When will my order ship? | 3 | 95 | F1, F6 |
| What is your return policy? | 4 | 61 | F3, F4 |
| How do I get my money back after a return? | 5 | 47 | F4 |
| Can I cancel my order? | 6, 7 | 93 | F9 |
| Can I change my shipping address? | 8 | 39 | F5 |
| Do you take PayPal? | 9 | 33 | F7 |
| Can I use a gift card to get cash? | 10 | 17 | F8 |
| Do your products have a warranty? | 11 | 58 | F10 |
| Do you ship internationally? | 12 | 26 | none (TO-CONFIRM) |

### Facts used

| Fact ID | Fact text |
|---|---|
| F1 | Orders ship within 2 business days after payment. |
| F2 | Standard shipping takes 5 to 7 business days within the continental United States. |
| F3 | Items may be returned within 30 days of delivery if unused and in original packaging. |
| F4 | Refunds go to the original payment method after the returned item is received and inspected. |
| F5 | Shipping address changes are accepted only before the order ships; contact support to request one. |
| F6 | A tracking number is emailed when the order ships. |
| F7 | We accept Visa, Mastercard, and PayPal. |
| F8 | Gift cards cannot be redeemed for cash. |
| F9 | Orders can be canceled before they ship. |
| F10 | All products carry a 1-year limited warranty against manufacturing defects. |

## Limits

- The 0.6 Jaccard threshold, the 60-word answer cap, and the 60-line intake cap are working values chosen for this skill. They are not published specifications.
- Merging uses word overlap with no stemming. "Ship" and "shipping" count as different words, so a question phrased with the other form can stay separate from its duplicate.
- Grouping and wording are judgment calls by the agent. Review the groups and answers before publishing.
- The JSON-LD block is checked for matching text and valid JSON only. It is not tested against any search engine's rich-result rules.
- A question that needs the facts of one customer's order is never answered and is listed as TO-CONFIRM.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
