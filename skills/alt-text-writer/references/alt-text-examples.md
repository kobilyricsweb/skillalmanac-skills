## Contents

- Sources
- Worked rewrites by function
- Long description template
- Markdown patterns

# Alt text examples and sources

Read the section that matches the image you are working on. Examples are original; facts about the standards are paraphrased from the pages listed.

## Sources

Pages behind the facts below (paraphrased, none copied):

- https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html : success criterion 1.1.1 requires a text alternative for non-text content that serves the same purpose; decoration may be ignored by assistive technology.
- https://www.w3.org/WAI/tutorials/images/ : the W3C image tutorial, with the categories informative, decorative, functional, image of text and complex that this skill's function table follows.
- https://www.w3.org/WAI/tutorials/images/decision-tree/ : the question order for choosing the alt rule.
- https://www.w3.org/WAI/WCAG22/Techniques/html/H67 : technique for hiding decoration with empty alt and no title.
- https://www.w3.org/WAI/WCAG22/Techniques/html/H2 : combine an image link and a text link for the same destination into one link.
- https://www.w3.org/WAI/WCAG22/Techniques/general/G94 and https://www.w3.org/WAI/WCAG22/Techniques/general/G92 : short text alternative for non-text content, and long description for it.

The 125-character working limit is not in any of these pages.

## Worked rewrites by function

| Function | Weak | Better | Reason |
|---|---|---|---|
| Informative | `alt="photo"` | `alt="Volunteers sorting donated coats in a church hall"` | Says what, who and where |
| Informative | `alt="Image of our new office"` | `alt="Reception desk and waiting area in the new Leeds office"` | No prefix; adds what matters |
| Decorative | `alt="blue wave"` | `alt=""` | Mood picture; page loses nothing |
| Functional | `alt="magnifying glass"` | `alt="Search"` | Action, not picture |
| Functional | `alt="Link to the pricing page"` | `alt="See pricing"` | Role is announced already |
| Text in image | `alt="Sale banner"` | `alt="Winter sale: 30% off coats until 31 January"` | Exact words |
| Complex | `alt="Chart"` | `alt="Line chart: weekly sign-ups rose from 12 to 48 between March and June"` | Type, subject, takeaway; data in long description |
| Logo as link | `alt="logo"` | `alt="Northwind home"` | Name and destination |

## Long description template

```
Description of the sign-ups chart
Purpose: shows weekly volunteer sign-ups so the reader sees the June jump.
Finding: sign-ups quadrupled between March and June.
Data: March 12, April 20, May 31, June 48 (weekly average).
Axes: months on the horizontal axis; sign-ups per week on the vertical axis.
Source: volunteer register, exported 2 July.
```

For a diagram, replace Data with a list of the parts in reading order and a line per connection ("Intake feeds Review; Review feeds either Approve or Return").

## Markdown patterns

- Informative: `![Volunteers sorting donated coats](img/coats.jpg)`
- Decorative: `![](img/divider.png)` (empty brackets mean empty alt)
- Linked: `[![See pricing](img/arrow.svg)](pricing.md)`
- Complex, with description underneath:

```
![Line chart: weekly sign-ups rose from 12 to 48 between March and June](img/signups.png)

<details><summary>Description of the sign-ups chart</summary>
March 12, April 20, May 31, June 48.
</details>
```

- A Markdown title in quotes after the path becomes a title attribute, not alt. Do not use it as the description.
