Required input fields:
- locale inventories listing keys and supplied values or explicit empty entries;
- explicit fallback edges or ordered fallback chains;
- terminal missing-key policy, if one is intended.

Optional inputs include requested locale-key pairs and source labels. If a locale, key inventory, fallback edge, or terminal policy is missing, state the gap and leave affected resolutions unresolved. If fallback rules conflict or form a cycle, preserve each rule and mark the affected paths ambiguous or cyclic.

The output must contain a resolution map with requested locale, key, status, source locale, fallback path, and notes. Follow only supplied edges. A missing key is not permission to use arbitrary English or another preferred locale. The map is an analysis artifact and does not modify resource files or determine application behavior beyond the documented policy.
