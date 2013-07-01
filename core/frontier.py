from Queue import Queue, Empty, Full
from threading import Thread, Lock
from datetime import datetime
import logging

class Frontier(object):
	"""
	A Frontier maintains URLs in two queues: front queue (used for input) and back queue (used for output).
	when put() is called, url is accepted and pushed into front queue directly. 
	There is a housecleaning thread which keeps moving url from the front queue to the back queue, if only the url is validate. 
	A url is considered validate if and only if all the registered eliminator functions produce False on it and the url hasn't been visited before.
	Everytime get() is called, an url is popped out from back queue.	
	"""
	
	def __init__(self, maxQSize, isDaemon = True):
		"""
		Initialize the Frontier object.
		"""
		super(Frontier, self).__init__()
		self.daemon = True
		self._frontQ = Queue(maxQSize)
		self._backQ = Queue(maxQSize)
		self._eliminators = []
		self._urlDupEliminator = DupEliminator()
		self._lock = Lock() #prevent from concurrent access to _housecleanThread
		self._housecleanThread = None

	def register(self, eliminateFunc):
		"""
		Register a eliminator function. 
		A eliminator function must take in a url and returns a bool to indicate whether the url should be eliminated.
		"""
		self._eliminators.append(eliminateFunc)

	def __elim(self, url):
		"""
		Check if a given url should be visited.
		---------  Param --------
		url: (str)  		
			The url to be checked.
		---------  Return --------
		(bool): True if url should be visited, false otherwise.
		"""
		for eliminateFunc in self._eliminators:
			if(eliminateFunc(url)):
				return True
		return self._urlDupEliminator.visitedBefore(url)

	def _houseclean(self):
		try:
			while(not self._frontQ.empty() and not self._backQ.full()):
				url = self._frontQ.get(timeout = 10)
				if not self.__elim(url):
					self._backQ.put(url, timeout = 2)	
		except:
			logging.getLogger().info("url front Q is empty or back Q is full. Will stop the housecleaning thread for a while")
		finally:
			self._housecleanThread = None

		
	def get(self, block = True, timeout = 10):
		if(self._backQ.empty() and not self._frontQ.empty()):
			self._lock.acquire()
			if(not self._housecleanThread):
				self._housecleanThread = Thread(target = self._houseclean)
				self._housecleanThread.daemon = True
				self._housecleanThread.start()
			self._lock.release()
		return self._backQ.get(block, timeout)

	def put(self, item, block = True, timeout = 2):
		return self._frontQ.put(item, block, timeout)

	def dump(self):
		self._urlDupEliminator.dump()
		return self._urlDupEliminator.size() - self._backQ.qsize()


class DupEliminator(object):
	"""
	A URLValidator is used to validate urls.
	"""
	def __init__(self):
		self._visited = set()
		self._lock = Lock()
		
	def visitedBefore(self, url):
		"""
		Check if a given url has been visited before.
		---------  Param --------
		url: (str)  		
			The url to be checked.
		---------  Return --------
		(bool): True if url has been visited before, false otherwise.
		"""
		self._lock.acquire()
		try:	
			visited = url in self._visited
			if(not visited):
				self._visited.add(url)
			return visited
		finally:
			self._lock.release() 

	def size(self):
		"""
		Return the number of downloaded pages so far.
		"""
		self._lock.acquire()
		try:	
			total = len(self._visited)
			return total
		finally:
			self._lock.release()

	def dump(self): #just for testing, will be removed eventually
		"""
		Dump the visited urls into ./log/visited.log
		"""
		import os
		if(not os.path.exists("log")):
			os.makedirs("log")
		output = open("log/visited.log", "w")
		self._lock.acquire()
		for item in self._visited:
			line = "%s : %s\n" %(datetime.now(), item.encode('utf8'))
			output.write(line)
		self._lock.release()
		