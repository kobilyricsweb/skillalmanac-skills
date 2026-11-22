# Which structured data earns a rich result

Status as read from Google Search Central on 2026-11-20 (see Sources). Features change; when network access is available, re-read the documentation changelog before telling a user that a feature exists.

## Contents

1. Status by type
2. Decision table by page kind
3. Rating and review policy
4. Sources and what was re-opened

## 1. Status by type

| Type | Status | Notes |
|---|---|---|
| Article, NewsArticle, BlogPosting | Earns | No required properties; headline, image, dates and author are recommended |
| BreadcrumbList | Restricted | Shown on desktop results only (since 22 Jan 2025) |
| Product (with offers, review or aggregateRating) | Earns | Pros and cons only on editorial product review pages |
| Review, AggregateRating (review snippet) | Earns, for a fixed list of reviewed types | Book, Course, Event, Movie, Product, Recipe, SoftwareApplication and some creative-work types; LocalBusiness and Organization only on sites that review other businesses |
| SoftwareApplication, WebApplication, MobileApplication | Earns | Needs name, offers.price, and aggregateRating or review |
| VideoObject | Earns, on watch pages | The video must be the page's main content |
| QAPage | Earns | Only pages with one question that users can answer |
| DiscussionForumPosting | Earns | User-generated threads only |
| ProfilePage | Earns | People or organisations affiliated with the site |
| Organization | Earns (logo and knowledge details) | On the home page or one about page |
| WebSite name / alternateName | Earns (site name) | Home page only |
| Event, Recipe, JobPosting, LocalBusiness, Course list, Movie, Vacation rental, Employer aggregate rating, Education Q&A, Math solver, Image metadata, Speakable, Subscription and paywalled content | Listed in the gallery | Not covered in depth here; read the type's own page |
| Carousel (ItemList) | Restricted | Host carousel only for course, movie, recipe and restaurant pages |
| Dataset | Restricted | Used by Dataset Search only |
| **FAQPage** | **Retired** | Limited to government and health sites in Sept 2023; no longer shown from 7 May 2026; documentation removed 15 June 2026 |
| **HowTo** | **Retired** | No longer shown since Sept 2023 |
| **WebSite SearchAction** (sitelinks search box) | **Retired** | Removed in late 2024 |
| **SpecialAnnouncement, course info, estimated salary, learning video, vehicle listing** | **Retired** | Documentation removed 9 Sept 2025 |
| **Practice problems (Quiz)** | **Retired** | Documentation removed 6 Jan 2026 |
| ClaimReview (fact check) | Being phased out | Banner added June 2025; absent from the gallery |
| WebPage, CollectionPage, ItemList (outside carousels), DefinedTerm, SoftwareSourceCode, TechArticle | Semantic only | Valid schema.org, no rich result of their own |

## 2. Decision table by page kind

| Page | Main type | Expect |
|---|---|---|
| Blog post, guide, news | Article (or NewsArticle, BlogPosting) | Article enhancements |
| Step-by-step guide | Article; steps stay as visible HTML | Nothing from HowTo |
| Page with an FAQ block | The page's real main type; FAQ stays as visible HTML | Nothing from FAQPage |
| Product page with first-party reviews | Product with offers, aggregateRating, review | Price, availability, stars |
| Editorial review of one product | Product with one Review by a named author | Review snippet |
| App or software page with user ratings | SoftwareApplication | Stars, price |
| App or software page without ratings | SoftwareSourceCode or WebPage | None; avoids a permanent "missing field" error |
| Category, list, "best of", comparison | CollectionPage or Article with ItemList | None; **no rating markup** |
| Community question with answers | QAPage | Q&A result |
| Site-written question and answer | Article or WebPage | None |
| Video watch page | VideoObject | Video result |
| Page that embeds a video among other content | The page's main type; VideoObject optional | Video result unlikely |
| Home | Organization and WebSite | Site name, logo |
| Author or member profile | ProfilePage | Profile details |
| Local business own site | LocalBusiness without self-collected star markup | Business details; no stars |

## 3. Rating and review policy

- The item reviewed is one specific thing and is the page's subject. Not a category, not a list.
- Ratings come from the site's own users or its own named reviewer. Do not aggregate ratings or reviews from other websites.
- An entity's reviews of itself (a business marking up testimonials about itself) are not eligible.
- `ratingValue`, `ratingCount` and `reviewCount` equal the numbers visible on the page. At least one count is required.
- `bestRating` defaults to 5 and `worstRating` to 1; state them when the scale differs.
- A site's own computed score (an editorial or automated grade) is not an aggregate of user ratings; do not place it in `aggregateRating`. On a page that is the review of one product, the reviewer's own score may be a single `Review` with a named `author` and `reviewRating` (state `bestRating` when the scale is not 5). On any other page it stays visible text.
- Fake reviews and undisclosed incentivised reviews are prohibited on the page and in markup.
- Review author names are under 100 characters and are real names or handles, not slogans.
- Breaking these rules can bring a manual action that removes rich-result eligibility; it does not by itself change normal ranking.

## 4. Sources and what was re-opened

Re-opened on 2026-11-20 for this version, all on `developers.google.com/search/`:

- `updates` (documentation changelog): the FAQ, llms.txt, breadcrumb, review-guideline, practice-problem, Dataset and September 2025 removal entries; the September 2023 HowTo and FAQ entries.
- `docs/appearance/structured-data/search-gallery`: the 25 listed features; FAQ and HowTo are absent.
- `docs/appearance/structured-data/review-snippet`: supported types, required properties, guidelines, rating defaults.
- `docs/appearance/structured-data/sd-policies`: formats, access, visibility, completeness, no guarantee of display, manual actions.

Taken from the research this skill was built from (read the same day, not re-opened here): the software-app, product-snippet, qapage, video, breadcrumb, carousel, article, organization, profile-page, discussion-forum and dataset pages. From memory, not re-opened: the date of the sitelinks search box removal. The search engine named here publishes the most detail; other engines' supported lists were not obtained.
