# import urllib2
import hashlib

class Page(object):
	"""
	A Page represents a web page.
	"""
	def __init__(self, url, content):
		"""
		Initialize a Page object by specifying its url and html content. The corresponding host, scheme and path are Initialized by parsing the url.
		e.g. Given the url = http://www.gnu.org/software/guile/, we would get a page as follows:
		HOST: www.gnu.org
		SCHEME: http
		PATH: /software/guile/
		"""
		self._url = url
		self._content = content
		# request = urllib2.Request(url)
		# self._host = request.get_host()
		# self._scheme = request.get_type()
		# self._path = request.get_selector()
		
	def getURL(self):
		return self._url

	def getContent(self):
		return self._content

	# def getHost(self):
	# 	return self._host

	# def getScheme(self):
	# 	return self._scheme

	# def getPath(self):
	# 	return self._path
		
	# def __hash__(self):
	# 	m = hashlib.md5()
	# 	m.update(self._url)
	# 	return m.hexdigest()

	# def __eq__(self, other):
	# 	return self._url == other._url

	# def __str__(self):
	# 	return "URL: %s\nHOST: %s\nSCHEME: %s\nPATH: %s" % (self._url, self._host, self._scheme, self._path)

