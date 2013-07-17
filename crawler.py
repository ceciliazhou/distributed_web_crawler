#!/usr/bin/python
import sys
from optparse import OptionParser
from core.engine import Engine, MAX_URL_QSIZE, DEFAULT_REG_PORT, DEFAULT_MANAGER, DEFAULT_DOWNLOADERS

def parseCommandLineArgs():
	parser = OptionParser()
	parser.add_option("-m", "--manager", dest="manager", default=DEFAULT_MANAGER,
	                  help="the name/ip of the host on which manager is started.")
	parser.add_option("-p", "--port", dest="regPort", default=DEFAULT_REG_PORT,
	                  help="port to connect manager.")
	parser.add_option("-d", "--download", dest="downloaders", default=DEFAULT_DOWNLOADERS,
	                  help="number of threads which download web pages. 4 by default.")
	(options, args) = parser.parse_args()

	return options.manager, int(options.regPort), int(options.downloaders)

def main():
	manager, port, downloaders  = parseCommandLineArgs()
	engine = Engine(downloaders, manager, port)
	engine.start()
	raw_input("press any key to stop....\n")
	engine.stop()

if __name__ == "__main__":
	main()