#!/usr/bin/python
"""Tests for the Frontier class."""

import unittest
from lib.frontier import Frontier
from Queue import Empty
import urllib2 
from threading import Thread
import time

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

    def test_frontier_with_multi_thread(self):
        keyFunc = lambda x : x/10
        filterFunc = lambda x : x%10 > 3
        numOfQ = 5
        f = Frontier(numOfQ, keyFunc=keyFunc)
        f.addFilter(filterFunc)
        for i in range(numOfQ):
            Thread(target=put_numbers, args=(f, 0, 49)).start()

        out = [] 
        threads = []
        for i in range(6):
            out.append([])
            t = Thread(target=get_numbers, args=(f, out[i]))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        result = []
        for i in range(6):
            result += out[i]
        result.sort()
        for i in range(len(result)):
            # assert continous output are from different groups
            assert(keyFunc(result[i][1]) == i%numOfQ)

    def test_frontier_with_url_file(self):
        f = Frontier(12, keyFunc= hostname)
        import os
        seeds = open(os.path.realpath("test/sample_input"), 'r')
        urls = []
        for line in seeds.readlines():
            f.put(line.strip())
        seeds.close()

        output = open("test/sample_output", "w")
        output.write("f.size() = "+str(f.size()) +"\n")
        while(f.size() > 0):
            item = f.get()
            item = "" if item is None else item
            line = item.encode('utf8') + "\n"
            output.write(line)
        output.close()


def put_numbers(F, min, max):
    for i in range(min, max+1):
        F.put(i)

def get_numbers(F, out):
    while(F.size() > 0):
        try:
            data = F.get(block=False)
            if data is not None:
                t = (time.time(), data)
                out.append(t)
        except Empty:
            pass

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
