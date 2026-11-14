"""Offline tests. Never connect to Claude or delete anything."""
import unittest
from unittest.mock import patch

from cleaner import sample_delay_seconds, validate_interval


class IntervalTests(unittest.TestCase):
    def test_invalid_ranges(self):
        for a, b in ((0, 1), (10, 2), (2, 200), (-1, 5)):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                validate_interval(a, b)

    def test_default_sample_bounds(self):
        for _ in range(100):
            self.assertGreaterEqual(sample_delay_seconds(2, 6), 2 * 3600)
            self.assertLessEqual(sample_delay_seconds(2, 6), 6 * 3600)

    def test_same_bounds(self):
        self.assertEqual(sample_delay_seconds(3, 3), 3 * 3600)

    def test_independent_sampling(self):
        values = [sample_delay_seconds(2, 6) for _ in range(8)]
        self.assertGreater(len(set(values)), 1)


if __name__ == "__main__":
    unittest.main()
