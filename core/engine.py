import os
import logging
import urllib2
import hashlib
import time
import zmq
import socket
from Queue import Queue
from threading import Thread, RLock, Timer, Event
from pymongo import MongoClient

from downloader import Downloader
from parser import Parser
from lib.frontier import Frontier
import urlFilter 

DEFAULT_MANAGER = "127.0.0.1"
DEFAULT_REG_PORT = 13000
DEFAULT_DB_PORT = 27017

DEFAULT_DOWNLOADERS = 4
MAX_URL_QSIZE = 10000
MAX_PAGE_QSIZE = 100

class Engine(object):
	"""
	A Engine starts working by starting a number of downloader threads and a number of parser threads. 
	It keeps crawling internet from a given set of seeds until being stopped.
	"""
	def __init__(self, nDownloader = DEFAULT_DOWNLOADERS, manager = DEFAULT_MANAGER, \
		regPort = DEFAULT_REG_PORT, dbPort = DEFAULT_DB_PORT, urlPort = None, pagePort = None):
		"""
		Initialize a crawler object.
		---------  Param --------
		nDownloader (int):
			the nubmer of downloader threads.
		manager:
			the host on which manager is started.
		regPort:
			the port on which manager expects connection requests.
		urlPort:
			the port on which this worker sends url to manager.
		pagePort:
			the port on which this worker sends page to manager.

		---------  Return --------
		None.
		"""
		## prepare the url frontier and page queue
		self._pageQ = Queue(MAX_PAGE_QSIZE)
		self._urlFrontier = Frontier(3*nDownloader, MAX_URL_QSIZE, \
					keyFunc=lambda url: urllib2.Request(url).get_host(), \
					priorityFunc=self.getLastVisitTime)
		self._visitSite = {}
		self._lock = RLock()
		self._stopEvent = Event()

		## prepare filters
		filetypeFilter = urlFilter.FileTypeFilter(True, ['text/html'])
		robotFilter = urlFilter.RobotFilter(Downloader.DEFAULT_USER_AGENT)
		self._urlDupEliminator = urlFilter.DupEliminator()
		self._urlFrontier.addFilter(filetypeFilter.disallow)
		self._urlFrontier.addFilter(self._urlDupEliminator.seenBefore)
		# self._urlFrontier.addFilter(robotFilter.disallow)
		
		## initialize sockets.
		self._manager = manager
		self._regPort = regPort
		self._urlPort = urlPort
		self._thisHost =  socket.gethostbyname(socket.gethostname())
		self._dbclient = MongoClient(manager, dbPort)
		context = zmq.Context()
		self._regSocket = context.socket(zmq.REQ)
		self._regSocket.connect("tcp://%s:%d" % (manager, self._regPort))
		self._urlPushSocket = context.socket(zmq.PUSH)

		self._urlPullSocket = context.socket(zmq.PULL)
		if(self._urlPort is None):
			self._urlPort = self._urlPullSocket.bind_to_random_port("tcp://%s" % self._thisHost)
		else:
			self._urlPullSocket.bind("tcp://*:%d" % (self._urlPort))

		## prepare log files
		if(not os.path.exists("log")):
			os.makedirs("log")
		self._logger = logging.getLogger("engine")
		self._logger.addHandler(logging.FileHandler(os.path.abspath("log/engine%d.log" % self._urlPort)))
		self._logger.setLevel(logging.WARNING)
		parseLogger = logging.getLogger("parser")
		parseLogger.addHandler(logging.FileHandler(os.path.abspath("log/parser.log")))
		parseLogger.setLevel(logging.WARNING)

		## create threads for downloading and parsing tasks
		self._downloaders = []
		for i in range(nDownloader):
			downloader = Downloader(self._urlFrontier, self._pageQ, self._logger, self.updateLastVisitTime)
			downloader.daemon = True
			self._downloaders.append(downloader)
		self._parser = Parser(self._pageQ, self._urlPushSocket, self._dbclient, parseLogger)

	def log(self, level, msg):
		"""
		Log info/warning/error message in log file.
		"""
		if(self._logger is not None):
			if level == logging.INFO:
				self._logger.info("[%s] INFO: %s" % (time.ctime(), msg))
			elif level == logging.WARNING:
				self._logger.warn("[%s] WARNING: %s" % (time.ctime(), msg))
			else:
				self._logger.error("[%s] ERROR: %s" % (tme.ctime(), msg))

	def _register(self):
		"""
		Request connection to master. 
		"""
		self._regSocket.send("REG %s %d" % (self._thisHost, self._urlPort))
		response = self._regSocket.recv()
		managerurlPort = response.split()[1]
		self.log(logging.INFO, "success to connect to manager:%s" % managerurlPort)
		self._urlPushSocket.connect("tcp://%s:%s" % (self._manager, managerurlPort))

	def start(self):
		"""
		Start crawling.
		"""
		print "[%s] : Crawler is started!" %time.ctime()
		self._register()
		self._dataAcceptor = Thread(target = self._recvData)
		self._dataAcceptor.daemon = True
		self._dataAcceptor.start()

		for downloader in self._downloaders:
			downloader.start()
		self._parser.start()

	def _recvData(self):
		"""
		Keeps listening to urlPort.
		Process each arrival data.
		"""
		while(not self._stopEvent.isSet()):
			urlSet = self._urlPullSocket.recv_pyobj()
			self.log(logging.INFO, "received %s" % urlSet)
			for url in urlSet:
				try:
					self._urlFrontier.put(url)
				except Full:
					time.sleep(5)

	def stop(self):
		"""
		Stop crawling.
		"""
		print "[%s] : Crawler is stopped!" %time.ctime()
		self._stopEvent.set()
		self._parser.stop()
		self._parser.join()
		self._dump()
		self._regSocket.send("UNREG %s %d" % (self._thisHost, self._urlPort))
		response = self._regSocket.recv()
		self.log(logging.INFO, "received %s" % response)
		
	def _dump(self):
		"""
		Dump the ready_to_be_crawled urls to log file.
		"""
		total = self._urlDupEliminator.size()
		left = self._urlFrontier.size()
		print "%d url discovered, but only %d downloaded and %d ready for downloading." %(total, total-left, left)

		unvisited = set()
		while(self._urlFrontier.size() > 0):
			unvisited.add(self._urlFrontier.get())

		self._urlPushSocket.send_pyobj(unvisited)
		unvisited.clear()
		
	def getLastVisitTime(self, site):
		"""
		Return the last time a site was visited. 
		"""
		self._lock.acquire()
		lastVT = 0 
		site = hashlib.sha1(site).hexdigest()
		if(self._visitSite.has_key(site)):
			lastVT = self._visitSite[site]
		self._lock.release()
		return lastVT

	def updateLastVisitTime(self, site):
		"""
		Return the last time a site was visited. 
		"""
		self._lock.acquire()
		site = hashlib.sha1(site).hexdigest()
		self._visitSite[site] = time.time()
		self._lock.release()
