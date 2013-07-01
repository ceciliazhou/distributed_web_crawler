from Queue import Queue, PriorityQueue, Empty, Full
# from threading import Thread, Lock
# from datetime import datetime
# import logging


class Frontier(object):
	"""
	Frontier comes with essentially the same funtionality a regular queue can provide but with much more flexibility by customize it 
	with different filters and priority functions. Filters are used to eliminate the unwanted items, while priority functions help determine
	to how much extent an item should be considered more important to be dealt with (i.e. to be extracted from the frontier). 

	Infrastructure:
								-------- input
								|
								v
						------------------------------------
						|prioritizers(NOT IMPLEMENTED)|
						------------------------------------
								|
						---------------------------------
						|	filterers		|
						---------------------------------
								|						
			  --------------------------------------------------------------------------------
			  |  		  |		|		|		|		  |
			----		---- 								----
			|___|		|___|								|___| 
			|___|		|___|		... front queues ....				|___|
			|___|		|___|								|___|                         
			  |  		  |  		|		|		|		  |
			  ---------------------------------------------------------------------------------
								|
						---------------------------------
						|	splitter			|
						---------------------------------
								|						
			  --------------------------------------------------------------------------------
			  |  		  |		|		|		|		  |
			----		---- 								----
			|___|		|___|								|___| 
			|___|		|___|		... back queues ....				|___|
			|___|		|___|								|___|                         
			  |  		  |  		|		|		|		  |
			  ---------------------------------------------------------------------------------
								|
						----------------------------------------
						|	back queue selector		|
						|					|
						|	-------------------------	|
						|  	|	map 		|	|     
						|	|key(item)  - backQref	|	|
						|	-------------------------	|
						|		^			|
						|		||			|
						|		v 			|
						|    	-------------------------	|
						|	|	maxHeap	|	|		
						|	|   priority(key(item))	|	|
						|	-------------------------	|
						-----------------------------------------

                                    

	Data members:
	_frontQ: Queue
		a queue containing whatever is put in the frontier.

	_backQ: list[ Queue ]
		a list of queues containing items to be extracted from the frontier.

	_prioritizer: list[ ( func(item), weight ) ]
		a list containing functions which produce importance of a given item. 
		Each function comes with a weight about how much the produced importance would be seriously considered.
		The final priority would be the sum of all the weighted importance. i.e. P(item) = sum(weight * func(item)) 
		The resulted priority determines to which front queue the item goes.
		DEFAUL: empyt list. That is saying all items will be of equal priority, thus, the there will be only one queue in _frontQ.

	_filter: list[ func(item) ]
		a list containing functions which tell whether a given item should be disgarded.
		DEFAUL: empyt list. That is saying no item would be filtered, thus, this frontier is no different from Queue.PriorityQueue.

	_keyFunc: func(item)
		a function which returns a key for a given item. 
		The key will be used by _map to locate the back queue in which to find/insert the item.
		Also it will be used by _extractPrioritizer to determine from which back queue to extract an item.
		DEFAUL: item.__hash__() 		

	_map: dict[ key(item) : queue# ]
		a table mapping an item to the number of the back queue in which it's stored.

	_backQselector: Queue.PriorityQueue(key(item))
		a priority queue used to determine from which back queue an item should be extracted. For each node, i.e. key(item),
		the key is determined by _extractPrioritizer.

	_extractPriorityFunc: func(key(item))
		a function which returns the priority indicating how much an item should be extracted from the queue 
		whose number is determined by key(item). 
		Every time get() is called on the frontier, an item is always extracted from the queue of the highest priority, 
		i.e. _backQ[ { key(item) | Max(_extractPriorityFunc(key(item))) } ] ???? NOT sure how to express it accurately.


	"""
	DEFAULT_MAX_SIZE = 1000

	def _defaultPriorityFunc(item):
		"""
		Default function used to determine the priority of an item. 
		"""
		return 0

	def __init__(self, numOfQ, maxQSize = DEFAULT_MAX_SIZE, extractPriorityFunc = _defaultPriorityFunc, keyFunc = hash):
		"""
		Initialize the frontier.
		"""
		self._numOfQ = numOfQ
		self._maxQsize = maxQSize
		self._frontQ = Queue(self._maxQsize)
		self._backQ = []
		for i in range(self._numOfQ):
			self._backQ.append(Queue(self._maxQsize))

		self._prioritizer = []
		self._filter = []
		self._keyFunc = keyFunc
		self._backQselector = PriorityQueue()
		self._extractPriorityFunc = extractPriorityFunc
		self._map = {}


	def addFilter(self, filterFunc):
		"""
		Register a filter function. 
		A filter function must take in an item and returns a bool to indicate whether the item should be eliminated.
		"""
		self._filter.append(filterFunc)

	def get(self):
		"""
		Return an item whose key is of the highest priority.
		"""
		# How fetcher interacts with back queue:
		# Repeat: 
		# 	(i) extract current root q of the heap (q is a back queue)
		# 	(ii) fetch URL u at head of q ...
		# until we empty the q we get. (i.e.: u was the last URL in q)
		
		# When we have emptied a back queue q, Repeat:
		# 	(i) pull URLs u from front queues and 
		# 	(ii) add u to its corresponding back queue ...
		# until we get a u whose host does not have a back queue.
		# Then put u in q and create heap entry for it.

		## TO BE DONE : accquire lock
		if(len(self._map) == 0):
			self._transfer()

		if(self._backQselector.empty()):
			for(p, k) in self._map.iteritems():
				self._backQselector.put(HeapNode(p, k))

		## TO BE DONE: raise an error if no item left available?
		que = self._backQselector.get() 
		item = que.get()
		if(que.empty()):
			self._map.pop(self._keyFunc(item))
			self._transfer()
		return item

	def put(self, item):
		"""
		Put an item into the front Q iff the item is not eliminated by any of the registered functions.
		"""
		for filterFunc in self._filter:
			if(filterFunc(item)):
				return
		self._frontQ.put(item)

	def _findEmptyBackQ(self):
		for i in range(len(self._backQ)):
			if(self._backQ[i].empty()):
				return i
		return len(self._backQ)

	def _transfer(self):
		"""
		Transfer items from front Q to back Q until the next item can not fit any back q or front Q is empty.
		"""
		## TO BE DONE: acquire lock
		while(not self._frontQ.empty()):
			item = self._frontQ.get()
			key = self._keyFunc(item)
			if(not self._map.has_key(key)):
				qID = self._findEmptyBackQ()	
				if(qID == len(self._backQ)):
					self._frontQ.put(item) 
					return
				self._map[key] = qID
				self._backQselector.put(HeapNode(self._extractPriorityFunc(key), key))

			que = self._backQ[self._map[key]]
			que.put(item)


class HeapNode(object):
	"""
	TO BE DONE
	"""
	def __init__(self, priority, value):
		self._priority = priority
		self._value = value

	def __lt__(self, other):
		return self._priority < other._priority

	def __eq__(selt, other):
		return self._priority == other._priority 

	def __str__(self):
		return "Priority = %d, %s" % (self._priority, self._value)


		
		