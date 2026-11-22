# Structured data fix: Plan Pilot (/app)

Page: https://www.planpilot.example/app   Subject: Plan Pilot (SoftwareApplication)
Markup: WebPage (main entity: the app), SoftwareApplication with AggregateRating, HowTo (kept, retired), Organization (no rating)
Expected result: SoftwareApplication stars and price (rich result eligible). HowTo: none (retired). Organization: none on this page; logo and name are used from the home page.
Left out on purpose:
- VideoObject: the video is one section of the page, not its main content, so a video result is unlikely here. Its uploadDate had no time zone and description and contentUrl are not on the page. Restore it on a dedicated watch page with a time zone.
- Organization aggregateRating (5 from 12): not visible anywhere on the page, and a company rating its own testimonials is not eligible.
- SoftwareApplication datePublished ("12/03/2026"): ambiguous format and no publish date is visible on the page.
- SoftwareApplication operatingSystem ("Web, iOS, Android"): not visible on the page.
- aggregateRating 4.9 / 1280: not on the page. Replaced with the visible figures 4.6 / 212.
- Team plan $6 per user per month: not added as a second Offer, because the Offer price cannot express "per user per month" cleanly. Only the free plan is marked up.
Visible-content check: ratingValue 4.6 and ratingCount 212 match "Rated 4.6 out of 5 by 212 users."; offer price 0 matches "Free for up to 5 people"; name, URL and step texts match the visible text.
Script: 0 FAIL, 1 WARN (HowTo retired, kept on purpose per the skill's rule not to delete working markup), 2 NOTE (operatingSystem left out on purpose; the main-entity note is resolved because WebPage.mainEntity points to the app).
Still to do:
- Confirm that the 212 ratings come from the site's own users and not from an app store or another site. If they come from elsewhere, remove aggregateRating.
- Confirm the logo is at least 112 x 112 px.
- Run the corrected markup through Google's rich-result test and the schema.org validator.
- After release, check the structured-data reports in Search Console for zero invalid items. Search Console errors may take days to clear.
- Valid markup does not guarantee a rich result.

Corrected JSON-LD (replace all four existing script blocks in the head with this one block):

```html
<script type="application/ld+json">
{"@context": "https://schema.org",
 "@graph": [
  {"@type": "WebPage", "@id": "https://www.planpilot.example/app#webpage",
   "url": "https://www.planpilot.example/app", "name": "Plan Pilot: shared team planner",
   "mainEntity": {"@id": "https://www.planpilot.example/app#software"}},
  {"@type": "SoftwareApplication", "@id": "https://www.planpilot.example/app#software",
   "name": "Plan Pilot", "url": "https://www.planpilot.example/app",
   "applicationCategory": "BusinessApplication",
   "image": "https://www.planpilot.example/img/planpilot.png",
   "offers": {"@type": "Offer", "name": "Free plan", "price": "0", "priceCurrency": "USD"},
   "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.6", "bestRating": "5", "worstRating": "1", "ratingCount": "212"}},
  {"@type": "HowTo", "@id": "https://www.planpilot.example/app#howto", "name": "How to set up Plan Pilot",
   "step": [{"@type": "HowToStep", "text": "Create a workspace"}, {"@type": "HowToStep", "text": "Invite your team"}]},
  {"@type": "Organization", "@id": "https://www.planpilot.example/#organization", "name": "Plan Pilot Inc",
   "url": "https://www.planpilot.example", "logo": "https://www.planpilot.example/img/logo.png"}
 ]}
</script>
```

Checker output on this block (full page, offline): 0 FAIL, 1 WARN, 2 NOTE, as listed above.
