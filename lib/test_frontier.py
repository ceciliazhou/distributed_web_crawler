"""Tests for the Frontier class."""

import unittest
from frontier import Frontier
from Queue import Empty


class FrontierTests(unittest.TestCase):

    def test_instantiation(self):
        f = Frontier(6)
        self.assertIsInstance(f, Frontier)

    def test_puts_with_no_filters(self):
        f = Frontier(6)

        f.put('http://google.com/')
        f.put('http://dropbox.com/')
        f.put('http://python.org/')

        self.assertEqual(list_queue(f._frontQ), [
            'http://google.com/',
            'http://dropbox.com/',
            'http://python.org/',
            ])

    def test_puts_with_one_filter(self):
        f = Frontier(6)
        f.addFilter(lambda url: 'd' in url)

        f.put('http://google.com/')
        f.put('http://dropbox.com/')
        f.put('http://python.org/')

        self.assertEqual(list_queue(f._frontQ), [
            'http://google.com/',
            'http://python.org/',
            ])

    def test_puts_with_three_filters(self):
        f = Frontier(6)
        f.addFilter(lambda url: 'd' in url)
        f.addFilter(lambda url: 'x' in url)
        f.addFilter(lambda url: 'e' in url)

        f.put('http://google.com/')
        f.put('http://dropbox.com/')
        f.put('http://python.org/')

        self.assertEqual(list_queue(f._frontQ), [
            'http://python.org/',
            ])


def list_queue(q):
    """Empty the `queue`, returning its contents as a list."""
    items = []
    while True:
        try:
            items.append(q.get(block=False))
        except Empty:
            break
    return items


if __name__ == '__main__':
    unittest.main()
