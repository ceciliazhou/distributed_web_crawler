import os
import logging
from datetime import datetime
from Queue import Queue
import urllib2
from threading import RLock, Timer
import hashlib
import time

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
		self._visitSite = {}
		self._lock = RLock()

		## prepare filters
		filetypeFilter = urlFilter.FileTypeFilter(True, ['text/html'])
		robotFilter = urlFilter.RobotFilter(Downloader.DEFAULT_USER_AGENT)
		self._urlDupEliminator = urlFilter.DupEliminator()
		self._urlQ.addFilter(filetypeFilter.disallow)
		# self._urlQ.addFilter(robotFilter.disallow)
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
		Timer(4, self._statistic).start()
		Timer(8, self._statistic).start()
		Timer(12, self._statistic).start()

	def stop(self):
		"""
		Stop crawling.
		"""
		print "[%s] : Crawler is stopped!" %datetime.now()
		self._statistic()
		self._dump()
		
	def _statistic(self):
		"""
		Output statistic info.
		"""
		total = self._urlDupEliminator.size()
		left = self._urlQ.size()
		print "%d url discovered, but only %d downloaded and %d ready for downloading." %(total, total-left, left)

	def _dump(self):
		"""
		Dump the ready_to_be_crawled urls to log file.
		"""
		import os
		if(not os.path.exists("log")):
			os.makedirs("log")
		output = open("log/readyToBeVisited.log", "w")
		
		while(self._urlQ.size() > 0):
			item = self._urlQ.get()
			self.updateLastVisitTime(urllib2.Request(item).get_host())
			item = "" if item is None else item
			line = item.encode('utf8') + "\n"
			output.write(line)
		output.close()
		
	def getLastVisitTime(self, site):
		"""
		Return the last time a site was visited. 
		"""
		self._lock.acquire()
		lastVT = 0 
		# site = hashlib.sha1(site).hexdigest()
		if(self._visitSite.has_key(site)):
			lastVT = self._visitSite[site]
		self._lock.release()
		return lastVT

	def updateLastVisitTime(self, site):
		"""
		Return the last time a site was visited. 
		"""
		self._lock.acquire()
		# site = hashlib.sha1(site).hexdigest()
		self._visitSite[site] = time.time()
		self._lock.release()
