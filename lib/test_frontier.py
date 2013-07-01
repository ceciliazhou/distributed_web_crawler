"""Tests for the Frontier class."""

import unittest
from frontier import Frontier
from Queue import Empty
import urllib2 

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

    def test_transfer_with_enough_backQs(self):
        f = Frontier(6, keyFunc = hostname)
        f.put('http://google.com/')
        f.put('http://dropbox.com/')
        f.put('http://google.com/index.html')
        f.put('http://python.org/')

        f._transfer()
        self.assertEqual(list_queue(f._backQ[0]), ['http://google.com/', 'http://google.com/index.html'])
        self.assertEqual(list_queue(f._backQ[1]), ['http://dropbox.com/'])
        self.assertEqual(list_queue(f._backQ[2]), ['http://python.org/'])
        self.assertEqual(list_queue(f._frontQ), [])

    def test_transfer_with_insufficient_backQs(self):
        f = Frontier(2, keyFunc = hostname)
        f.put('http://google.com/')
        f.put('http://dropbox.com/')
        f.put('http://google.com/index.html')
        f.put('http://python.org/')

        f._transfer()
        self.assertEqual(list_queue(f._backQ[0]), ['http://google.com/', 'http://google.com/index.html'])
        self.assertEqual(list_queue(f._backQ[1]), ['http://dropbox.com/'])
        self.assertEqual(list_queue(f._frontQ), ['http://python.org/'])

    def test_get_with_no_filter(self):
        f = Frontier(2, keyFunc = hostname)
        f.put('http://dropbox.com/')
        f.put('http://google.com/')
        f.put('http://google.com/index.html')
        f.put('http://python.org/')

        self.assertEqual(f.get(), 'http://dropbox.com/')
        self.assertEqual(f.get(), 'http://google.com/')
        self.assertEqual(f.get(), 'http://python.org/')
        self.assertEqual(f.get(), 'http://google.com/index.html')
        self.assertEqual(list_queue(f._frontQ), [])
        
    def test_get_with_filter(self):
        f = Frontier(6, keyFunc = lambda x : x/10)
        f.addFilter(lambda x : x%10 == 0)

        for i in range(50):
            f.put(i)

        for j in range(1, 10):
                for i in range(5):
                    self.assertEqual(f.get(), i*10+j)
        self.assertEqual(list_queue(f._frontQ), [])

    def test_get_with_filter_but_insufficient_backQs(self):
        f = Frontier(6, keyFunc = lambda x : x%10)
        f.addFilter(lambda x : x/10 == 3)

        for i in range(50):
            f.put(i)

        for i in range(50):
            if i/10 != 3:
                    self.assertEqual(f.get(), i)
        self.assertEqual(list_queue(f._frontQ), [])

def hostname(url):
        req= urllib2.Request(url)
        return req.get_host()


def list_queue(q):
    """Empty the `queue`, returning its contents as a list."""
    items = []
    while True:
        try:
            items.append(str(q.get(block=False)))
        except Empty:
            break
    return items


if __name__ == '__main__':
    unittest.main()
