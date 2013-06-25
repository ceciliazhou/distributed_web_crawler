from Queue import Queue
from threading import Thread, Event, Lock


class Frontier(Thread):
	"""
	A Frontier maintains URLs in two queues: front queue (used for input) and back queue (used for output).
	when put() is called, url is accepted and pushed into front queue directly. 
	There is a house-keeping thread which keeps moving url from the front queue to the back queue, if only the url is validate. 
	A url is considered validate if and only if all the registered validation functions produce True on it and the url hasn't been visited before.
	Everytime get() is called, an url is popped out from back queue.	
	"""
	
	def __init__(self):
		"""
		Initialize the Frontier object.
		"""
		super(Frontier, self).__init__()
		self._frontQ = Queue()
		self._backQ = Queue()
		self._stopEvent = Event()
		self._eliminators = []
		self._urlDupEliminator = DupEliminator()

	def register(self, eliminateFunc):
		"""
		Register a validation function. 
		A validation function must take in a url and returns a bool to indicate whether the url is considered valid.
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

	def run(self):
		while(not self._stopEvent.is_set()):
			url = self._frontQ.get(timeout = 10)
			if not self.__elim(url):
				self._backQ.put(url, timeout = 2)	
			
	def stop(self):
		self._stopEvent.set()
		self._urlDupEliminator.dump()

	def get(self, block = True, timeout = 10):
		return self._backQ.get(block, timeout)

	def put(self, item, block = True, timeout = 2):
		return self._frontQ.put(item, block, timeout)

	def countDownloadedPages(self):
		return self._urlDupEliminator.size()


class DupEliminator(object):
	"""
	A URLValidator is used to validate urls.
	"""
	def __init__(self):
		super(DupEliminator, self).__init__()
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

	def dump(self):
		"""
		Dump the visited urls into ./log/visited.log
		"""
		import os
		if(not os.path.exists("log")):
			os.makedirs("log")
		output = open("log/visited.log", "w")
		for item in self._visited:
			output.write(item + "\n")
			
		