This pattern works in my Python tests. It will run in a browser (JavaScript) form validator, so I need it there:

    (?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])$

Inputs like 2026-11 should match. The whole field is checked. Tell me honestly what you could and could not test.
