# Answer key: InviteMembers.tsx (check each in the code)

Data loading
1. Effect keyed on teamId with AbortController or ignore flag in cleanup
2. res.ok checked; errors caught; AbortError not shown as an error
3. Loading, error (with retry or message) and empty states for the list
4. When teamId changes, old invites are not shown as if they belonged to the new team (reset or loading state), and chips/form state is reset or deliberately kept and stated
Form
5. Email validation with a clear message; duplicates rejected (case-insensitive, and ideally against already-pending invites)
6. Chips stored as a list of strings or objects with stable keys (the email itself is a fine key); no index keys
7. No mutation (no push/splice on state); updater form where the previous value is needed
8. Submit: pending state, button disabled or guarded against double submit, error shown, success clears chips and updates or refetches the list
9. No derived state stored (e.g. isValid, count) and no effect used to sync state
Accessibility
10. Input has a label; error tied by aria-describedby / aria-invalid; remove buttons are buttons with names including the email
11. Status and errors announced (role=status / role=alert / aria-live)
12. Form submits on Enter via a real form element; Enter or comma adds a chip without submitting accidentally
Types
13. No `any`; invite type declared; status as a union rather than several contradictory booleans (booleans acceptable if they cannot contradict)
Defects to penalise: async function passed to useEffect; missing cleanup; fetch in render; key={index}; setState during render; unhandled promise.
