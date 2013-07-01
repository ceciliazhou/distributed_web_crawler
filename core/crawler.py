#!/usr/bin/python
import sys
from optparse import OptionParser
from engine import Engine

DEFAULT_SEEDS = "http://en.wikipedia.org"
DEFAULT_DOWNLOADERS = 4
DEFAULT_PARSERS = 1

def parseCommandLineArgs():
	parser = OptionParser()
	parser.add_option("-s", "--seeds", dest="seeds", default=DEFAULT_SEEDS,
	                  help="the web sites from which to start crawling")
	parser.add_option("-d", "--download", dest="downloaders", default=DEFAULT_DOWNLOADERS,
	                  help="number of threads which download web pages. ")
	# parser.add_option("-p", "--parser", dest="parsers", default=1,
	#                   help="number of threads which parse web pages to extract links. (recommend: d/10???")
	(options, args) = parser.parse_args()
	seeds = options.seeds
	seeds = seeds.split()
	return seeds, int(options.downloaders), DEFAULT_PARSERS  # int(options.parsers)

def main():
	seeds, downloaders, parsers  = parseCommandLineArgs()
	engine = Engine(seeds, downloaders, parsers)
	engine.start()
	raw_input("press any key to stop....\n")
	engine.stop()

if __name__ == "__main__":
	main()