#!/usr/bin/python
import sys
from optparse import OptionParser
from core.engine import Engine

DEFAULT_SEEDS = "conf/seeds.cfg"
DEFAULT_DOWNLOADERS = 4
DEFAULT_PARSERS = 1

def parseCommandLineArgs():
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="file", default=DEFAULT_SEEDS,
	                  help="the file which contains the web sites from which to start crawling, ./conf/seeds.cfg is used by default.")
	parser.add_option("-d", "--download", dest="downloaders", default=DEFAULT_DOWNLOADERS,
	                  help="number of threads which download web pages. 4 by default.")
	# parser.add_option("-p", "--parser", dest="parsers", default=DEFAULT_PARSERS,
	#                   help="number of threads which parse web pages to extract links. (recommend: d/10???")
	(options, args) = parser.parse_args()
	fname = options.file
	f = open(options.file, "r")
	seeds = []
	for line in f.readlines():
		seeds.append(line.strip())
	f.close()
	return seeds, int(options.downloaders),  DEFAULT_PARSERS 

def main():
	seeds, downloaders, parsers  = parseCommandLineArgs()
	engine = Engine(seeds, downloaders, parsers)
	engine.start()
	raw_input("press any key to stop....\n")
	engine.stop()

if __name__ == "__main__":
	main()