import unittest

from checkout.cart import cart_total


class CartTests(unittest.TestCase):
    def test_gold_cart(self):
        self.assertEqual(cart_total([{"price_cents": 1000, "qty": 2}], {"tier": "gold"}), 1700)


if __name__ == "__main__":
    unittest.main()
