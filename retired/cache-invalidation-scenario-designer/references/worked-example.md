Synthetic input:

Key product:{id} stores an individual product. Key category:{id} stores a category list. A product update invalidates only product:{id}. The stated staleness tolerance is zero. No relationship between products and category lists is supplied, and no readers are supplied.

Concrete artifact:

| Mutation | Key | Timing | Reader | Staleness | Status |
|---|---|---|---|---|---|
| product update | product:{id} | unspecified | missing reader input | 0 | specified key relationship; timing gap |
| product update | category:{id} | unspecified | missing reader input | 0 | relationship gap |

The category-list case remains unresolved because no product-to-category-key rule was supplied. Both reader values remain missing because no readers were supplied. Verification checked the one stated key relationship and the zero-tolerance allowance; it did not infer hidden dependencies or runtime freshness.
