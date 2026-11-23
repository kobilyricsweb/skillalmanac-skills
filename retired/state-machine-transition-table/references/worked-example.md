Synthetic input:
States: Draft; Published.
Event: publish.
Guard note: publish is allowed only from Draft.
Effect note: set publication timestamp.
No note describes publishing from Published, and no destination is stated for any other event.

Actual artifact:

| Source | Event | Guard | Destination | Effect | Status |
|---|---|---|---|---|---|
| Draft | publish | allowed only from Draft | Published | set publication timestamp | documented |
| Published | publish | not supplied | — | — | unspecified |

Unresolved cases: the notes do not define other events, transitions from Published, or whether repeated publication should be rejected. Assumption: “publication timestamp” is recorded when the documented transition occurs; its format and replacement behavior are unspecified. The table does not infer a denial for Published + publish.
