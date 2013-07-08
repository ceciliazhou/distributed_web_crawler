#!/usr/bin/python
"""
Run all the tests. (currently there is only one test on the library frontier.)
"""

import unittest
from test.TestFrontier import FrontierTests


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(FrontierTests)
	unittest.TextTestRunner().run(suite)