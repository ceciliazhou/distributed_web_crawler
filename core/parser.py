from bs4 import BeautifulSoup
from Queue import Queue, Empty, Full
from threading import Thread, Event
from datetime import datetime 
from urlparse import urlparse, urljoin
import zmq
import chardet

import os
import logging 
# from page import Page
import sys

MIN_PAGE_MSG_SIZE = 5
MIN_URL_MSG_SIZE = 20

class Parser(Thread):
	"""A Parser is a thread that keep parsing html pages and extracting links to other web pages."""
	
	def __init__(self, pageQ, dataSocket, dbConn, logger = None):
		"""
		Initialize a parser object.
		---------  Param --------
		pageQ: (Queue)  		
			A queue storing the pages to be parsed.
		urlOut: (Queue) 
			A queue used for the parser to store the urls exatracted from pages.
		logger: (logging.Logger)
			A logger used to log info/warning/error about parsing.

		---------  Return --------
		None.
		"""
		super(Parser, self).__init__()
		self._pageQ = pageQ
		self._urlOut = set()
		self._pageOut = []
		self._logger = logger
		self._dataPushSocket =dataSocket
		self._dbclient = dbConn
		self._stopEvent = Event()

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
			parser = BeautifulSoup(page["html"])
			for link in parser.findAll('a'):
				if link.has_attr('href'):
					url = link['href']
					url = urljoin(page["url"], url)
					if(urlparse(url).hostname is not None):
						links.append(url)
		except:
			self.log(logging.WARNING, "Unable to parse " + page)
		return links

	def stop(self):
		self._stopEvent.set()

	def run(self):
		"""
		Start parsing.
		"""
		while(not self._stopEvent.isSet()):
			try:
				page = self._pageQ.get(timeout = 5)
				for link in self.parse(page):
					self._urlOut.add(link)
					if(len(self._urlOut) >= MIN_URL_MSG_SIZE):
						self._dataPushSocket.send_pyobj(self._urlOut)
						self.log(logging.INFO, "sending %s" % self._urlOut)
						self._urlOut.clear()

				self._storePage(page)
			except Empty:
				self.log(logging.INFO, "pageQ is empty") 

		while(not self._pageQ.empty()):
			self._storePage(self._pageQ.get(timeout = 1))
				
	def _storePage(self, page):
		"""
		Store the url and html in database.
		"""
		try:
			charset = page["charset"]
			if charset is not None and charset.lower() != "utf-8":
				page["html"] = page["html"].decode(charset, errors='ignore')
				page["html"] = page["html"].encode("utf-8", errors='ignore')
			page.pop('charset')
			self._dbclient.crawler.webpage.insert(page)
		except :
			self.log(logging.WARNING, "failed to store webpage %s" % page["url"])