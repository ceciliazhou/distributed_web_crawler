from Queue import Queue, PriorityQueue, Empty, Full
from time import time
from threading import Thread, RLock


DEFAULT_MAX_SIZE = 1000
DEFAULT_TIME_OUT = 2

class Frontier(object):
	"""
	Frontier comes with essentially the same funtionality a regular queue can provide but with much more flexibility by customize it 
	with different filters and priority functions. Filters are used to eliminate the unwanted items, while priority functions help determine
	to how much extent an item should be considered more important to be extracted from the frontier). 

	Infrastructure:
								-------- input
								|
								v
						---------------------------------
						|	filterers		|
						---------------------------------
								|						
			  --------------------------------------------------------------------------------                      
			  |  		  		front  queue		  			 |
			  --------------------------------------------------------------------------------
								|
						---------------------------------
						|	splitter (by key(item))	|
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
						|	|	minHeap	|	|		
						|	|   priority(key(item))	|	|
						|	-------------------------	|
						-----------------------------------------

                                    

	Data members:
	_frontQ: PeekableQ
		a queue containing whatever is put in the frontier.

	_backQ: list[ Queue ]
		a list of queues containing items to be extracted from the frontier.

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

	_priorityFunc: func(key(item))
		a function which returns the priority indicating how much an item should be extracted from the queue 
		whose number is determined by key(item). The smaller returned value means the higher priority.
		Every time get() is called on the frontier, an item is always extracted from the queue of the highest priority, 
		i.e. _backQ[ { key(item) | Min(_priorityFunc(key(item))) } ] ???? NOT sure how to express it accurately.
	"""

	def _defaultPriorityFunc(item):
		"""
		Default function used to determine the priority of an item. 
		"""
		return time()

	def __init__(self, numOfQ, maxQSize = DEFAULT_MAX_SIZE, keyFunc = hash, priorityFunc = _defaultPriorityFunc):
		"""
		Initialize the frontier.
		"""
		self._frontQ = PeekableQ(maxQSize)
		self._backQ = []
		for i in range(numOfQ):
			self._backQ.append(Queue(maxQSize))

		self._filter = []
		self._keyFunc = keyFunc
		self._backQselector = PriorityQueue()
		self._priorityFunc = priorityFunc
		self._map = {}
		self._lock = RLock()


	def addFilter(self, filterFunc):
		"""
		Register a filter function. 
		A filter function must take in an item and returns a bool to indicate whether the item should be eliminated.
		"""
		self._filter.append(filterFunc)

	def get(self, block=True, timeout=DEFAULT_TIME_OUT):
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
		self._lock.acquire()
		if(len(self._map) == 0):
			self._transfer()

		if(self._backQselector.empty()):
			for(p, k) in self._map.iteritems():
				self._backQselector.put(HeapNode(self._priorityFunc(p), p))

		if(self._backQselector.empty()):
			self._lock.release()
			return
		key = self._backQselector.get(block, timeout).getValue() ## may raise Empty 
		que = self._backQ[self._map[key]]  
		item = que.get(block, timeout)
		if(que.empty()):
			self._map.pop(self._keyFunc(item))
			self._transfer()
		self._lock.release()
		return item

	def put(self, item, block=True, timeout=0):
		"""
		Put an item into the front Q iff the item is not eliminated by any of the registered functions.
		"""
		for filterFunc in self._filter:
			if(filterFunc(item)):
				return
		self._frontQ.put(item, block, timeout)

	def _firstEmptyBackQ(self):
		self._lock.acquire()
		for i in range(len(self._backQ)):
			if(self._backQ[i].empty()):
				self._lock.release()
				return i
		self._lock.release()
		return len(self._backQ)

	def _transfer(self):
		"""
		Transfer items from front Q to back Q until the next item can not fit any back q or front Q is empty.
		"""
		self._lock.acquire()
		while(not self._frontQ.empty()):
			item = self._frontQ.peek()
			key = self._keyFunc(item)
			if(not self._map.has_key(key)):
				qID = self._firstEmptyBackQ()	
				if(qID == len(self._backQ)):
					self._lock.release()
					return
				self._map[key] = qID
				self._backQselector.put(HeapNode(self._priorityFunc(key), key))

			que = self._backQ[self._map[key]]
			que.put(self._frontQ.get())
		self._lock.release()

	def size(self):
		"""
		Return the number of items in the Frontier.
		"""
		self._lock.acquire()
		sz = self._frontQ.qsize()
		for q in self._backQ:
			sz += q.qsize()
		self._lock.release()
		return sz

	def dump(self):
		"""
		TO BE DONE
		"""
		self._lock.acquire()
		urls = []
		while(not self._frontQ.empty()):
			urls.append(self._frontQ.get())
		for q in self._backQ:
			while(not q.empty()):
				urls.append(q.get())
		self._lock.release()
		return urls


class HeapNode(object):
	"""
	HeapNode is a simple data structure which can be used in a priority queue. 
	It has a priorty and an associated value. The priority is the key which will be used for sorting.
	"""
	def __init__(self, priority, value):
		self._priority = priority
		self._value = value

	def getValue(self):
		return self._value

	def __lt__(self, other):
		return self._priority < other._priority

	def __eq__(selt, other):
		return self._priority == other._priority 

	def __str__(self):
		return "Priority = %d, %s" % (self._priority, self._value)

class PeekableQ(object):
	"""
	PeekableQ is a FIFO queue. 
	In addition to the methods availiable in Queue.Queue, it also provides a peek() method which returns the head item in the queue 
	without popping it out.
	"""
	def __init__(self, maxSize = DEFAULT_MAX_SIZE):
		self._Q = Queue(maxSize)
		self._front = None
		self._capacity = maxSize
		self._lock = RLock()

	def get(self, block = False, timeout = DEFAULT_TIME_OUT):
		"""
		Pop and return the item at the front of the queue.
		"""
		self._lock.acquire()
		if(self._front is not None):
			ret = self._front
			self._front = None
			self._lock.release()
			return ret
		else:
			self._lock.release()
			return self._Q.get(block, timeout) 

	def peek(self):
		"""
		Return the item at the front of the queue.
		"""
		self._lock.acquire()
		if(self._front is None and not self._Q.empty()):
			self._front = self._Q.get()
		self._lock.release()
		return self._front
		
	def put(self, item, block = False, timeout = DEFAULT_TIME_OUT):
		"""
		Push an item into the queue from the back.
		"""
		self._Q.put(item, block, timeout)

	def empty(self):
		"""
		Return True if the queue is empty, False otherwise.
		"""
		self._lock.acquire()
		result = self._Q.empty() and self._front is None
		self._lock.release()
		return result

	def full(self):
		"""
		Return True if the queue is full, False otherwise.
		"""
		return self.qsize() >= self._capacity
		
	def qsize(self):
		"""
		Return the number of items in the queue.
		"""
		self._lock.acquire()
		sz = self._Q.qsize()
		if(self._front is not None):
			sz += 1
		self._lock.release()
		return sz