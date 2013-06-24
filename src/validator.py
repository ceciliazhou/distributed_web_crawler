from threading import Lock

class URLValidator(object):
	"""
	A URLValidator is used to validate urls.
	"""
	def __init__(self):
		super(URLValidator, self).__init__()
		self._visited = set()
		self._lock = Lock()
		
	def validate(self, url):
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
			result = (url not in self._visited)
			if(result):
				self._visited.add(url)
			return result
		finally:
			self._lock.release() 

	def countDownloadedPages(self):
		"""
		Return the number of downloaded pages so far.
		"""
		self._lock.acquire()
		try:	
			total = len(self._visited)
			return total
		finally:
			self._lock.release()