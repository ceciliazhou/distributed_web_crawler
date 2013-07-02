import os
import logging
from datetime import datetime
from Queue import Queue
import urllib2
from threading import RLock
import hashlib

from downloader import Downloader
from parser import Parser
from lib.frontier import Frontier
import urlFilter 

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
		## prepare the url frontier and page queue
		self._pageQ = Queue(MAX_PAGE_QSIZE)
		self._urlQ = Frontier(3*nDownloader, MAX_URL_QSIZE, \
					keyFunc=lambda url: urllib2.Request(url).get_host(), \
					priorityFunc=self.getLastVisitTime)
		self._visitTime = {}
		self._lock = RLock()

		## prepare filters
		filetypeFilter = urlFilter.FileTypeFilter(True, ['text/html'])
		robotFilter = urlFilter.RobotFilter(Downloader.DEFAULT_USER_AGENT)
		self._urlDupEliminator = urlFilter.DupEliminator()
		self._urlQ.addFilter(filetypeFilter.disallow)
		self._urlQ.addFilter(robotFilter.disallow)
		self._urlQ.addFilter(self._urlDupEliminator.seenBefore)
		for seed in seeds:
			self._urlQ.put(seed)
		
		## prepare log files
		if(not os.path.exists("log")):
			os.makedirs("log")
		downloadLogger = logging.getLogger("downloader")
		downloadLogger.addHandler(logging.FileHandler(os.path.abspath("log/download.log")))
		downloadLogger.setLevel(logging.INFO)
		parseLogger = logging.getLogger("parser")
		parseLogger.addHandler(logging.FileHandler(os.path.abspath("log/parser.log")))
		parseLogger.setLevel(logging.INFO)
				
		## create threads for downloading and parsing tasks
		self._downloaders = []
		for i in range(nDownloader):
			downloader = Downloader(self._urlQ, self._pageQ, downloadLogger, self.updateLastVisitTime)
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
		num = self._urlDupEliminator.size() - self._urlQ.size()
		print num, " pages downloaded!"
		print self._urlQ.dump()
		
	def getLastVisitTime(self, site):
		"""
		Return the last time a site was visited. 
		"""
		self._lock.acquire()
		lastVT = 0 
		site = hashlib.sha1(site).hexdigest()
		if(self._visitTime.has_key(site)):
			lastVT = self._visitTime(site)
		self._lock.release()
		return lastVT

	def updateLastVisitTime(self, site):
		"""
		Return the last time a site was visited. 
		"""
		self._lock.acquire()
		lastVT = 0 
		site = hashlib.sha1(site).hexdigest()
		self._visitTime[site] = time.time()
		self._lock.release()
		return lastVT
