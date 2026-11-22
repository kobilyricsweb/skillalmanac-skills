Problem: locale inventories can conceal missing keys and unclear fallback paths. Artifact: a per-locale resolution map showing source locale, path, missing keys, cycles, and ambiguities. Audience: localization engineers and reviewers. Practical limits: it follows only declared edges, preserves unresolved cases, and does not edit resources, invent translations, or claim runtime behavior.

Unpublished editorial tier: free. No score or release approval.

Scope distinction: configuration-key-drift-check validates config names; this resolves locale resource keys through explicitly declared fallback chains.
