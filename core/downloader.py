"""
TO BE DONE
"""

import urllib2
import chardet
from Queue import Queue, Empty, Full
from threading import Thread
from datetime import datetime 
import logging
import time
import sys

# from page import Page

class Downloader(Thread):
	DEFAULT_USER_AGENT = "User-Agent: Mozilla/5.0"

	"""
	A Downloader is a thread that keeps downloading web pages until it's stopped.
	"""

	def __init__(self, urlIn, pageQ, logger = None, userAgent = DEFAULT_USER_AGENT, callbackFun = None):
		"""
		Initialize a Downloader.
		---------  Param --------
		urlIn: (Queue) 
			A queue storing the urls from which web pages are to be downloaded.
		pageQ: (Queue)  		
			A queue used for the downloader to store the downloaded pages.
		logger: (logging.Logger)
			A logger used to log info/warning/error about downloading.
		userAgent: (str) 
			A string to set the user agent field in a HTTP request header.

		---------  Return --------
		None
		"""
		super(Downloader, self).__init__()
		self._urlIn = urlIn
		self._pageQ = pageQ
		self._userAgent = userAgent
		self._logger = logger
		self._callbackFun = callbackFun

	def log(self, level, msg):
		"""
		Log info/warning/error message in log file.
		"""
		if(self._logger is not None):
			if level == logging.INFO:
				self._logger.info("[%s] INFO: %s" % (datetime.now(), msg))
			elif level == logging.WARNING:
				self._logger.warn("[%s] WARNING: %s" % (datetime.now(), msg))
			else:
				self._logger.error("[%s] ERROR: %s" % (datetime.now(), msg))
		
	def download(self, url):
		"""
		Download a web page from url.
		---------  Param --------
		url: (str) 	
			The url of the web page to be downloaded.

		---------  Return --------
		(str) The html contents of the web page.
		"""
		try:
			self.log(logging.INFO, "downloading file: "+url)
			request = urllib2.Request(url)
			request.add_header('User-Agent', self._userAgent)
			page = urllib2.urlopen(request)
			if(self._callbackFun is not None):
				self._callbackFun(request.get_host())
			html = page.read()
			if(html is not None):
				contentType = page.info().get("content-type")
				charset =  contentType.split("charset=")[-1]
				if contentType.find("charset") == -1:
					charset = chardet.detect(html)['encoding']
				return {"url":url, "html":html, "charset":charset}
		except:
			self.log(logging.WARNING, str(sys.exc_info()[0]) + "Unable to open " + url)


	def run(self):
		"""
		Start downloading.
		"""
		while(True):
			try:
				url = self._urlIn.get(timeout = 2)
				if url is not None:
					page = self.download(url)
					if page and (not self._pageQ.full()):
						self._pageQ.put(page, timeout = 2)
			except Empty:
				self.log(logging.INFO, "urlIn is empty") 
				time.sleep(5)
			except Full:
				self.log(logging.INFO, "pageQ is full") 
				time.sleep(5)
