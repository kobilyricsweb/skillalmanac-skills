Support ticket 5521: "The orders screen opens on page 1 but shows orders 11 to 20. Orders 1 to 10 only appear on page 0, which the UI does not offer. The users screen is fine."

Repro: with 25 orders numbered 1..25, `list_orders(orders, page=1, size=10)` returns orders 11..20; expected 1..10.
