About
------------
This web crawler consists of a manager and a bunch of workers which can work in single-node mode or cluster mode. Each worker downloads web pages and communicates the server with urls extracted from the downloaded pages. Manager is responsible for scheduling crawling tasks among the workers with consideration of load balance. Manager also handles dynamically connected/disconnected workers. 

Installation Dependencies
------------
Before you can run this crawler, you may need to download and install:

1. [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/bs4/download/)
2. [zmq core lib](http://zeromq.org/area:download) and [pyzmq](http://zeromq.org/bindings:python)
3. [mongodb](http://docs.mongodb.org/manual/installation/) and [pymongo](http://api.mongodb.org/python/current/installation.html)


Try it:
--------
1. Start the manager on master node.

		Usage: crawlerManager.py [options]
		Options:
		  -h, --help            show this help message and exit
		  -f FILE, --file=FILE  the file which contains the web sites from which to
		                        start crawling, ./conf/seeds.cfg is used by default.
		  -p REGPORT, --port=REGPORT
		                        port on which connection requests are expected.
		  -d URLPORT, --urlPort=URLPORT
		                        port on which urls are sent to workers.

2. Start workers on master or any other hosts.

		Usage: crawlerWorker.py [options]
		Options:
		  -h, --help            show this help message and exit
		  -m MANAGER, --manager=MANAGER
		                        the name/ip of the host on which manager is started.
		  -p REGPORT, --port=REGPORT
		                        port to connect manager.
		  -d DOWNLOADERS, --download=DOWNLOADERS
		                        number of threads which download web pages. 4 by
		                        default.

Design:
------------
![design.png](https://raw.github.com/ceciliazhou/distributed_web_crawler/master/design.png)