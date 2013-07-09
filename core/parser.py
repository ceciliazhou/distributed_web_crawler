from bs4 import BeautifulSoup
from Queue import Queue, Empty, Full
from threading import Thread
from datetime import datetime 
from urlparse import urlparse, urljoin

import os
import logging 
from page import Page

class Parser(Thread):
	"""A Parser is a thread that keep parsing html pages and extracting links to other web pages."""
	
	def __init__(self, pageQ, urlQ, logger = None):
		"""
		Initialize a parser object.
		---------  Param --------
		pageQ: (Queue)  		
			A queue storing the pages to be parsed.
		urlQ: (Queue) 
			A queue used for the parser to store the urls exatracted from pages.
		logger: (logging.Logger)
			A logger used to log info/warning/error about parsing.

		---------  Return --------
		None.
		"""
		super(Parser, self).__init__()
		self._pageQ = pageQ
		self._urlQ = urlQ
		self._logger = logger

	def log(self, level, msg):
		"""
		Log info/warning/error message in log file.
		"""
		if level == logging.INFO:
			self._logger.info("[%s] INFO: %s" % (datetime.now(), msg))
		elif level == logging.WARNING:
			self._logger.warn("[%s] WARNING: %s" % (datetime.now(), msg))
		else:
			self._logger.error("[%s] ERROR: %s" % (datetime.now(), msg))

	def parse(self, page):
		"""
		Parse a web page.
		---------  Param --------
			page: (Page) 	
				A Page object whose content is to be parsed.

		---------  Return --------
			(list) The links this page leads to.
		"""
		links = []
		try:
			parser = BeautifulSoup(page.getContent())
			for link in parser.findAll('a'):
				if link.has_attr('href'):
					url = link['href']
					url = urljoin(page.getURL(), url)
					if(urlparse(url).hostname is not None):
						links.append(url)
		except:
			self.log(logging.WARNING, "Unable to parse " + page)
		return links

	def run(self):
		"""
		Start parsing.
		"""
		while(True):
			try:
				page = self._pageQ.get(timeout = 5)
				for link in self.parse(page):
					self._urlQ.put(link, timeout = 2)
			except Empty:
				self.log(logging.WARNING, "pageQ is empty") 
			except Full:
				self.log(logging.WARNING, "urlQ is full") 
				
	