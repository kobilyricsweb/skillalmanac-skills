dump of everything on "saved carts" - from slack + the tuesday call

#product-ideas
Hana (PM): analytics says 23% of mobile sessions add something to the cart and leave without buying. A lot of them come back on desktop and the cart is empty.
Leo (support lead): we get about 40 tickets a month that are basically "where did my cart go". All logged-in users btw, guests don't write in.
Hana: so idea = cart is saved to the account and shows up on any device.

#eng-web
Marta (eng lead): carts live in the browser session today. Saving to the account is doable. Guest users are a different story, we have nothing to attach the cart to. Guest carts cannot be in v1.
Marta: we'd need to decide what happens when the price changed or the item is out of stock when they come back.
Dev (designer): I'd show a small notice on the item, "price changed" / "no longer available". Not a popup.

Tuesday call notes (Hana)
- CEO wants this live "for the holidays"
- Leo: keep saved carts for 30 days, after that people don't remember them anyway
- Marta: 90 days is what the loyalty team asked for, they want to send reminder emails
- nobody decided between 30 and 90
- reminder emails: loyalty team wants them, Hana says not in the first version, separate project
- Dev asked if the cart should merge when you add things on two devices. Everyone said yes, merge, keep the higher quantity
- Marta: needs to work on web and the iOS app. Android app is being rewritten, skip it for now
- no one mentioned what number we want to hit
