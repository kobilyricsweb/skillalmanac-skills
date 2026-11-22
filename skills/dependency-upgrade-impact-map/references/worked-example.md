Synthetic input:

Old notes permit parseLegacy(). New notes remove parseLegacy(). Supplied usage references say importer calls parseLegacy() and exporter calls parse(). No other usage list is supplied.

Concrete artifact:

| Documented change | Usage site | Exposure | Required review |
|---|---|---|---|
| parseLegacy() removed | importer | directly exposed | review importer migration |
| parseLegacy() removed | exporter calling parse() | not matched to this change | no review implied by this note |

Unverified exposure: the supplied usage list may be incomplete. The artifact does not claim breakage or safety. Verification: the removed symbol was compared with each named usage reference, and coverage was limited to the supplied list.
