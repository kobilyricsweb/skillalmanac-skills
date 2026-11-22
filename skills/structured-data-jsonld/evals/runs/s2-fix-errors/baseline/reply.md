# Structured data fix: Plan Pilot app page

Source page: `s2_app_page.html` (canonical https://www.planpilot.example/app)

## Errors found and what changed

1. **SoftwareApplication `image` is a relative URL** (`/img/planpilot.png`). Google needs an absolute URL. Changed to `https://www.planpilot.example/img/planpilot.png`.
2. **SoftwareApplication `datePublished` is not ISO 8601** (`12/03/2026`). Changed to `2026-03-12`. This reads the value as day/month, because `2026-12-03` would be a future date (today is 2026-11-20). Confirm this date with the owner.
3. **Rating does not match the visible page.** Markup says 4.9 from 1,280 ratings, but the page text says "Rated 4.6 out of 5 by 212 users." Google requires review and rating markup to match what users see. The markup now uses 4.6 and 212 to match the page. If 4.9 / 1,280 is the true figure, the page text must be updated instead, and the markup kept. The owner must confirm which is correct.
4. **Rating values were strings** ("4.9", "1280"). Changed to numbers, as schema.org expects. `ratingCount` replaces the non-matching count so it matches the visible "212 users".
5. **Organization `aggregateRating` removed.** Google does not show rating snippets for Organization, and this one contradicted the page (5 from 12 reviews). Ratings belong only on the SoftwareApplication.
6. **Pricing missing.** The page states a free tier (up to 5 people) and a Team plan at $6 per user per month. Added two `Offer` entries so the markup matches the page. The currency is assumed to be USD from the "$" sign.
7. **VideoObject missing `description`.** Added a description drawn from the page text. Google lists `description` as required for video.
8. **VideoObject missing `embedUrl` / `contentUrl`.** Google's video documentation requires one of these. The page has only a "[embedded video]" placeholder and no video URL, so none was added. The owner must supply the real video URL (embed or content) and add it as `embedUrl` (or `contentUrl`).
9. **HowTo: no change.** The markup matches the visible steps and is valid. Google stopped showing HowTo rich results in 2023, so this markup gives no rich result. It can stay or be removed.

## Corrected JSON-LD

```html
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "SoftwareApplication", "@id": "https://www.planpilot.example/app#app", "name": "Plan Pilot",
 "applicationCategory": "BusinessApplication", "operatingSystem": "Web, iOS, Android",
 "image": "https://www.planpilot.example/img/planpilot.png", "datePublished": "2026-03-12",
 "offers": [
   {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD", "description": "Free for up to 5 people"},
   {"@type": "Offer", "name": "Team", "price": "6", "priceCurrency": "USD", "description": "Team plan, per user per month"}
 ],
 "aggregateRating": {"@type": "AggregateRating", "ratingValue": 4.6, "ratingCount": 212}}
</script>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "HowTo", "name": "How to set up Plan Pilot",
 "step": [{"@type": "HowToStep", "text": "Create a workspace"}, {"@type": "HowToStep", "text": "Invite your team"}]}
</script>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "VideoObject", "name": "Plan Pilot in 60 seconds",
 "description": "A 60-second overview of Plan Pilot, the shared planner for small teams.",
 "thumbnailUrl": "https://www.planpilot.example/img/video-thumb.jpg", "uploadDate": "2026-10-01T09:00:00"}
</script>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "Organization", "name": "Plan Pilot Inc", "url": "https://www.planpilot.example",
 "logo": "https://www.planpilot.example/img/logo.png"}
</script>
```

## Open items for the owner

- Confirm the rating: 4.6 from 212 (used here, matches the page) or 4.9 from 1,280 (then the page text must change).
- Confirm `datePublished` (2026-03-12 assumed).
- Confirm the currency (USD assumed) and that the $6 Team price is per user per month.
- Supply the video URL for `embedUrl` (or `contentUrl`) so the VideoObject is complete.
- After deploying, re-test with the Rich Results Test and check the Search Console enhancement reports.
