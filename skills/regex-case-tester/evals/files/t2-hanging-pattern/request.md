Our signup service validates usernames with this pattern, used with re.search:

    ^([a-z0-9]+[._-]?)+$

Some requests with long usernames such as "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!" make a worker spin at 100% CPU. Valid usernames look like ann, bob_smith, j.doe-2. Invalid ones include "", "-ann", "ann--bob", "a b". Fix the pattern, keep it Python re, and show proof.
