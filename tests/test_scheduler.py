"""Offline schedule checks. No Claude account, browser or deletion required."""
import unittest

from cleaner import sample_delay_seconds, validate_interval, is_due


class SchedulerTests(unittest.TestCase):
    def test_first_check_due(self):
        self.assertTrue(is_due({}, 1000))

    def test_before_deadline(self):
        self.assertFalse(is_due({"next_due_at": 1001}, 1000))

    def test_on_deadline(self):
        self.assertTrue(is_due({"next_due_at": 1000}, 1000))

    def test_interval(self):
        for _ in range(100):
            seconds = sample_delay_seconds(2, 6)
            self.assertGreaterEqual(seconds, 7200)
            self.assertLessEqual(seconds, 21600)

    def test_invalid_interval(self):
        for a, b in [(0, 2), (9, 2), (2, 200)]:
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                validate_interval(a, b)


if __name__ == "__main__":
    unittest.main()
