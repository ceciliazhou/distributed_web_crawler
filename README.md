This is a simple web crawler. It downloads and parses web pages starting with a given set of web sites which is called seeds. 

###Usage:
	
	python crawler.py [options]
	
	Options:
	  -h, --help
		show this help message and exit

  	  -f FILE, --file=FILE  
  	  	the file which contains the web sites from which to start crawling
 
	  -d DOWNLOADERS, --download=DOWNLOADERS
		number of threads which download web pages

	  -p PARSERS, --parser=PARSERS
		number of threads which parse web pages to extract links

	
###Desgin:
	
	Engine
		The main component of a crawler. The job of an engine consists of:
		1. initializes two queues: urlQ storing urls, pageQ storing downloaded web pages.
		2. starts/stops the configured number of downloader threads and parser threads.
	
	Downloader
		Downloader keeps fetching url from the urlQ and downloading web pages located that url only if the url hasn't been visited before.
		Everytime a pages is downloaded, it will be put into the pageQ for parsing.
	
	Parser
		Parser keeps fetching page from pageQ and exacting links by parsing the html tags.
		All the extracted links will be put into the urlQ for downloading.
	
	Frontier
		Frontier maintains urls in two queues: frontQ (input) and backQ (output)
		1. url is accepted (by put()) and pushed into frontQ if only the url survives the registered filter routines, includeing duplicate eliminator.
		2. url is grouped by host in backQ. That is, each queue in backQ corresponds to one site. 
		3. url is always extracted (by get()) from the group which has the highest priority. This is. important because we can configure as the priority the last time we visited the site corresponding to the group/queue, so that we always exact a url of the site hasn't been visited for the longest time.
		4. The Frontier is designed for general purpose, not specific for the crawler. For more details, please check out core.frontier.
