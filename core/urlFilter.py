from robotparser import RobotFileParser
from urlparse import urljoin
import mimetypes
import urllib2
import hashlib
from threading import Lock
from datetime import datetime


class RobotFilter(object):
	"""
	TO BE DONE
	"""
	def __init__(self, userAgent):
		self._userAgent = userAgent
		self._dict = {}
		
	def disallow(self, url):
		"""
		TO BE DONE
		"""
		robotFile = urljoin(url, "/robots.txt")
		if(not self._dict.has_key(robotFile)):
			self._dict[robotFile] = RobotFileParser(robotFile)
			try:
				self._dict[robotFile].read()
			except :
				self._dict[robotFile] = None
		try:
			return self._dict[robotFile] is not None and not self._dict[robotFile].can_fetch(self._userAgent, url)
		except:
			return True
	
class FileTypeFilter(object):
 	"""
 	TO BE DONE
 	"""
 	def __init__(self, allowOrDisallow = True, filterList = None):
 		self._allow = allowOrDisallow
 		self._filterList = filterList if filterList else []

 	def disallow(self, url):
		"""
		TO BE DONE
		"""
		fileType = mimetypes.guess_type(url)[0]
		if(self._allow == (fileType in self._filterList)):
			return False
		try:
			return not url.endswith(urllib2.Request(url).get_host()) and not url.endswith(urllib2.Request(url).get_host()+'/')
		except:
			return True

class DupEliminator(object):
	"""
	A URLValidator is used to validate urls.
	"""
	def __init__(self):
		self._visited = set()
		self._lock = Lock()
		
	def seenBefore(self, url):
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
			url = hashlib.sha1(url).hexdigest()
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

	# def dump(self): #just for testing, will be removed eventually
	# 	"""
	# 	Dump the visited urls into ./log/visited.log
	# 	"""
	# 	import os
	# 	if(not os.path.exists("log")):
	# 		os.makedirs("log")
	# 	output = open("log/visited.log", "w")
	# 	self._lock.acquire()
	# 	for item in self._visited:
	# 		line = item.encode('utf8') + "\n"
	# 		output.write(line)
	# 	self._lock.release()
	# 	