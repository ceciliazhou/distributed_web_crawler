import os
import logging
from datetime import datetime
from Queue import Queue

from downloader import Downloader
from parser import Parser
from frontier import Frontier

MAX_URL_QSIZE = 10000
MAX_PAGE_QSIZE = 100

class Engine(object):
	"""
	A Engine starts working by starting a number of downloader threads and a number of parser threads. 
	It keeps crawling internet from a given set of seeds until being stopped.
	"""
	def __init__(self, seeds, nDownloader, nParser):
		"""
		Initialize a crawler object.
		---------  Param --------
		seeds (list(str)):
			a list of urls from which to crawl the inernet.
		nDownloader (int):
			the nubmer of downloader threads.
		nParser:
			the number of parser threads.

		---------  Return --------
		None.
		"""
		self._urlQ = Frontier(MAX_URL_QSIZE)
		self._pageQ = Queue(MAX_PAGE_QSIZE)
		for seed in seeds:
			self._urlQ.put(seed)
		
		if(not os.path.exists("log")):
			os.makedirs("log")
		downloadLogger = logging.getLogger("downloader")
		downloadLogger.addHandler(logging.FileHandler(os.path.abspath("log/download.log")))
		downloadLogger.setLevel(logging.INFO)
		parseLogger = logging.getLogger("parser")
		parseLogger.addHandler(logging.FileHandler(os.path.abspath("log/parser.log")))
		parseLogger.setLevel(logging.INFO)
				
		self._downloaders = []
		for i in range(nDownloader):
			downloader = Downloader(self._urlQ, self._pageQ, downloadLogger)
			downloader.daemon = True
			self._downloaders.append(downloader)
		self._parsers = []
		for i in range(nParser):
			parser = Parser(self._pageQ, self._urlQ, parseLogger)
			parser.daemon = True
			self._parsers.append(parser)

	def start(self):
		"""
		Start crawling.
		"""
		print "[%s] : Crawler is started!" % datetime.now()
		for downloader in self._downloaders:
			downloader.start()
		for parser in self._parsers:
			parser.start()

	def stop(self):
		"""
		Stop crawling.
		"""
		print "[%s] : Crawler is stopped!" %datetime.now()
		print self._urlQ.dump(), " pages downloaded!"


