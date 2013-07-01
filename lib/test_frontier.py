"""Tests for the Frontier class."""

import unittest
from frontier import Frontier


class FrontierTests(unittest.TestCase):

    def test_instantiation(self):
        f = Frontier(6)
        self.assertIsInstance(f, Frontier)


if __name__ == '__main__':
    unittest.main()
