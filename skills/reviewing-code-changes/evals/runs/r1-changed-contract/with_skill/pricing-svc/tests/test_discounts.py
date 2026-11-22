import unittest

from pricing.discounts import calculate_discount


class DiscountTests(unittest.TestCase):
    def test_gold(self):
        self.assertIsNotNone(calculate_discount(10000, "gold"))

    def test_silver(self):
        self.assertAlmostEqual(calculate_discount(10000, "silver"), 0.10)


if __name__ == "__main__":
    unittest.main()
