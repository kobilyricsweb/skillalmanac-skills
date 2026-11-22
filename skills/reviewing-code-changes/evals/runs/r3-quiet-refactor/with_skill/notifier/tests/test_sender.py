import unittest
from unittest import mock

from notifier import sender


class SenderTests(unittest.TestCase):
    def test_retries_then_succeeds(self):
        with mock.patch.object(sender, "post", side_effect=[ConnectionError(), {"ok": True}]):
            self.assertEqual(sender.send({"to": "a"}), {"ok": True})

    def test_batch(self):
        with mock.patch.object(sender, "post", return_value={"ok": True}):
            self.assertEqual(len(sender.send_batch([{}, {}])), 2)

    def test_gives_up_after_three(self):
        with mock.patch.object(sender, "post", side_effect=ConnectionError()):
            with self.assertRaises(ConnectionError):
                sender.send({"to": "a"})


if __name__ == "__main__":
    unittest.main()
