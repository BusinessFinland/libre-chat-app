import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from versions import in_range, is_release, parse  # noqa: E402


class Versions(unittest.TestCase):
    def test_release_sorts_after_its_rcs(self):
        self.assertLess(parse("v0.8.9-rc1"), parse("v0.8.9"))
        self.assertLess(parse("v0.8.8"), parse("v0.8.9-rc1"))

    def test_is_release(self):
        self.assertTrue(is_release("v0.8.9"))
        self.assertFalse(is_release("v0.8.9-rc1"))
        self.assertFalse(is_release("chart-1.2.3"))

    def test_comma_ranges(self):
        spec = ">= 0.7.9, <= 0.8.8, < 0.8.9"
        self.assertFalse(in_range("v0.7.8", spec))
        self.assertTrue(in_range("v0.8.0", spec))
        self.assertFalse(in_range("v0.8.9", spec))

    def test_upper_bound_only(self):
        self.assertTrue(in_range("v0.7.8", "< 0.8.9"))
        self.assertFalse(in_range("v0.8.9", "< 0.8.9"))
        self.assertTrue(in_range("v0.8.9-rc1", "<= 0.8.9-rc1, < 0.8.9"))

    def test_hyphen_and_alternatives(self):
        self.assertTrue(in_range("v0.7.8", "v0.0.6 - v0.7.8"))
        self.assertFalse(in_range("v0.7.9", "v0.0.6 - v0.7.8"))
        self.assertTrue(in_range("v0.8.8", "= 0.7.0 || = 0.8.8"))

    def test_bare_version_is_equality(self):
        self.assertTrue(in_range("v0.8.8", "0.8.8"))


if __name__ == "__main__":
    unittest.main()
