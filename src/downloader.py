"""
TO BE DONE
"""

import urllib2
from Queue import Queue, Empty, Full
from threading import Thread, Event
from datetime import datetime 
import os
import logging

from page import Page

class Downloader(Thread):
	DEFAULT_USER_AGENT = "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0"

	"""
	A Downloader is a thread that keeps downloading web pages until it's stopped.
	"""

	def __init__(self, urlQ, pageQ, logger = None, userAgent = DEFAULT_USER_AGENT):
		"""
		Initialize a Downloader.
		---------  Param --------
		urlQ: (Queue) 
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
		self._urlQ = urlQ
		self._pageQ = pageQ
		self._userAgent = userAgent
		self._stopEvent = Event()
		self._logger = logger

	def log(self, level, msg):
		"""
		Log info/warning/error message in log file.
		"""
		if(self._logger):
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
		            request = urllib2.Request(url)
		            request.add_header('User-Agent', self._userAgent)
		            page = urllib2.urlopen(request)
		            content = page.read()
		            page.close()
		            if(content):
		            	return Page(url, content)
		except:
			self.log(logging.WARNING, "Unable to open " + url)

	def run(self):
		"""
		Start downloading.
		"""
		# index = 0
		while(not self._stopEvent.is_set()):
			try:
				url = self._urlQ.get(timeout = 2)
				page = self.download(url)
				# index += 1
				# page = page if page else ""
				# temp.write(page)
				# temp.close()
				# print page
				if page and (not self._pageQ.full()):
					self._pageQ.put(page, timeout = 2)
			
			except Empty:
				self.log(logging.WARNING, "urlQ is empty") 
			except Full:
				self.log(logging.WARNING, "pageQ is full") 

		# self.log(logging.INFO, str(index) + " pages downloaded")
				
	def stop(self):
		"""
		Stop downloading.
		"""
		self._stopEvent.set()
		