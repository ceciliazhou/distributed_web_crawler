#!/usr/bin/python
"""
TO DO
"""

import zmq
# from pymongo import MongoClient
import chardet
import os
import logging
import time
from threading import Thread, RLock
from urlparse import urlparse

DEFAULT_REG_PORT = 13000
DEFAULT_DATA_PORT = 13001
DEFAULT_DB_PORT = 27017
MIN_MSG_DATA = 5

class Manager(object):
	"""
	A manager accepts connections from worker workers, updates workers' info,
	collect data from connected workers and dispatch jobs among them in a load-balanced way.

	Data Members:
	_workerInfo: dict{ workerID: data_port, push_socket, last_update_time, assigned_sites, url_to_crawl }
		workerID: str, made up of the name or ip of the worker worker and its port.
		socket: zmq.Context.socket, a socket used to send data to worker.
		assigned_sites: set, the jobs already done by the worker.
		url_to_crawl: Queue, the jobs to be sent to the worker.
	"""
	def __init__(self, initialData = None, registerPort = DEFAULT_REG_PORT, urlPort = DEFAULT_DATA_PORT, dbPort = DEFAULT_DB_PORT):
		"""
		Initialize the manager object.
		"""
		self._regPort = registerPort
		self._urlPort = urlPort
		self._workerInfo = {}
		self._workerIDs = []
		self._buffer = set() if initialData is None else initialData
		self._lock = RLock()

		## prepare logger
		if(not os.path.exists("log")):
			os.makedirs("log")
		self._logger = logging.Logger("manager")
		self._logger.addHandler(logging.FileHandler(os.path.abspath("log/manager.log")))
		self._logger.setLevel(logging.WARNING)

		## initialize sockets.
		self._context = zmq.Context()
		self._regSocket = self._context.socket(zmq.REP)
		self._regSocket.bind("tcp://*:%d" % self._regPort)
		self._dataPullSocket = self._context.socket(zmq.PULL)
		self._dataPullSocket.bind("tcp://*:%d" % self._urlPort)

	def _log(self, level, msg):
		"""
		Log a message.
		"""
		if(self._logger is not None):
			if level == logging.INFO:
				self._logger.info("[%s] INFO: %s" % (time.ctime(), msg))
			elif level == logging.WARNING:
				self._logger.warn("[%s] WARNING: %s" % (time.ctime(), msg))
			else:
				self._logger.error("[%s] ERROR: %s" % (time.ctime(), msg))

	def start(self):
		"""
		Starts the three threads: 
		- listening connection requests 
		- receiving data and store it to the buffer.
		- partition data and deliverying it to the responding worker.
		"""
		connAcceptor = Thread(target = self._acceptConnections)
		connAcceptor.daemon = True
		connAcceptor.start()
		dataReceiver = Thread(target = self._recvData)
		dataReceiver.daemon = True
		dataReceiver.start()
		dataProcessor = Thread(target = self._processData)
		dataProcessor.daemon = True
		dataProcessor.start()


	def _acceptConnections(self):
		"""
		Keeps listening to _regPort. 
		On each arrival connection request, accepts and replies with the port number on which manager expects data.
		"""
		while(True):
			connectionReq = self._regSocket.recv()
			req, host, port = connectionReq.split()
			self._log(logging.INFO, "Received %s request from %s which expects data on %s" % (req, host, port))
			workerID = host + ":" + port
			if(req.upper() == "REG"):
				self._workerIDs.append(workerID)
				self._workerInfo[workerID] = {}
				dataPushSocket = self._context.socket(zmq.PUSH)
				dataPushSocket.connect("tcp://%s:%s" % (host, port))
				self._workerInfo[workerID]["socket"] = dataPushSocket
				self._workerInfo[workerID]["assigned_sites"] = set()
				self._workerInfo[workerID]["url_to_crawl"] = set()
				self._log(logging.INFO, "sending port number [%d] to %s" % (self._urlPort, workerID))
				self._regSocket.send("REG_RESPONSE %d" % self._urlPort)
			else: ## UNREG
				self._workerIDs.remove(workerID)
				if(self._workerInfo.has_key(workerID)):
					workerinfo = self._workerInfo.pop(workerID)
					workerinfo["socket"].close()
				self._regSocket.send("UNREG_RESPONSE success")

	def _recvData(self):
		"""
		Keeps listening to urlPort.
		Process each arrival data report and dispatch jobs if necessary, 
		e.g. when getting enough data for dispatching a job to some worker.
		"""
		while(True):
			msgType = self._dataPullSocket.recv()
			if self._dataPullSocket.getsockopt(zmq.RCVMORE):
				self._log(logging.INFO, "received %s" % (msgType))
				data = self._dataPullSocket.recv_pyobj()
				if msgType.upper() == "URL":
					self._lock.acquire()
					self._buffer.update(data)
					self._lock.release()

	def _processData(self):
		"""
		Process data (a set of data) received from worker workers.
		"""
		## TO DO: 
		## 1. workerdataSet.put(data)
		## 2. only if the workerdataSet is filled with enough data, send out to the responding worker worker.
		while(True):
			if(len(self._buffer) == 0 or len(self._workerInfo) == 0):
				time.sleep(2)
				continue

			self._lock.acquire()
			while(len(self._buffer) > 0):
				url = self._buffer.pop()
				site = urlparse(url).hostname
				targetworker = self._matchWorker(site)
				self._workerInfo[targetworker]["assigned_sites"].add(site)
				targetSet = self._workerInfo[targetworker]["url_to_crawl"]
				targetSet.add(url)
				if(len(targetSet) >= MIN_MSG_DATA):
					targetSocket = self._workerInfo[targetworker]["socket"]
					targetSocket.send_pyobj(targetSet)
					self._log(logging.INFO, "sending to %s: %s" % (targetworker, targetSet))
					self._workerInfo[targetworker]["assigned_sites"].update(targetSet)
					targetSet.clear()
			self._lock.release()

	def _matchWorker(self, site):
		"""
		A fake method to decide to which worker the site should go.
		"""
		## 1. check if anyone is already responsible for this site.
		## 2. if nobody found in step 1, match the site to a target worker by hashing.
		for worker, workerinfo in self._workerInfo.iteritems():
			if(site in workerinfo["assigned_sites"]):
				return worker

		workerID = hash(site) % len(self._workerIDs)
		return self._workerIDs[workerID]

DEFAULT_SEEDS = "conf/seeds.cfg"

def parseCommandLineArgs():
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="file", default=DEFAULT_SEEDS,
	                  help="the file which contains the web sites from which to start crawling, ./conf/seeds.cfg is used by default.")
	parser.add_option("-p", "--port", dest="regPort", default=DEFAULT_REG_PORT,
	                  help="port on which connection requests are expected.")
	parser.add_option("-d", "--urlPort", dest="urlPort", default=DEFAULT_DATA_PORT,
	                  help="port on which urls are sent to workers.")
	(options, args) = parser.parse_args()
	fname = options.file
	f = open(options.file, "r")
	seeds = set()
	for line in f.readlines():
		seeds.add(line.strip())
	f.close()
	return seeds, int(options.regPort), int(options.urlPort)

def main():
	seeds, regPort, urlPort  = parseCommandLineArgs()
	Manager(seeds, regPort, urlPort).start()
	raw_input("press any key to stop....\n")
			
if __name__ == "__main__":
	main()