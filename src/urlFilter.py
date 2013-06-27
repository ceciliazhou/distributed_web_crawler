from robotparser import RobotFileParser
from urlparse import urljoin
import mimetypes
import urllib2

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
			self._dict[robotFile].read()
		return not self._dict[robotFile].can_fetch(self._userAgent, url)
	
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
		return  urllib2.Request(url).get_selector() != ""
	