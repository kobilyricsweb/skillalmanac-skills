# Answer key: settings.fixed.html (check each in the source)

Dialog
1. Uses native dialog with showModal(), or role=dialog + aria-modal=true
2. Has an accessible name (aria-labelledby the title, which should be a heading, or aria-label)
3. Focus moves into the dialog on open
4. Focus contained: native showModal, or a Tab trap, or background inert
5. Escape closes it
6. Focus returns to the "Delete this workspace" trigger on close
7. Trigger is a button (or a link with href and keyboard handling); close X is a button with a name such as "Close"
Other widgets
8. Theme chooser: native select with a label, or a custom listbox with button aria-haspopup/aria-expanded, role=listbox/option, arrow keys, Escape, and a label
9. Weekly summary switch: checkbox or button role=switch with aria-checked updated, keyboard operable, and tied to its text label
10. Toast: live region (role=status or aria-live) present in the DOM before the message is inserted
11. Confirm-name field: real label (not only placeholder); wrong name gives a text error tied to the field (aria-invalid + aria-describedby or role=alert), not only a red border
12. Focus indicator restored (the *:focus outline 0 rule removed or replaced with a visible :focus-visible style)
Preservation
13. Same visual design and same behaviours (toggle saves, theme picks, delete confirm flow)
Defects to penalise: aria-hidden on a container with focusable content; role without keyboard support; positive tabindex; toast region created at the moment of the message only; removing features.
