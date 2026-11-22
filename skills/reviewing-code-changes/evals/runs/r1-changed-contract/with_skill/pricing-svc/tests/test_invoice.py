import unittest

from billing.invoice import invoice_total


class InvoiceTests(unittest.TestCase):
    def test_no_tier_pays_full(self):
        self.assertEqual(invoice_total(20000, "none"), 20000)


if __name__ == "__main__":
    unittest.main()
