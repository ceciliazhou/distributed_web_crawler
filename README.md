This is a simple web crawler. It downloads and parses web pages starting with a given set of web sites which is called seeds. 

###Usage:###
	
	python crawler.py [options]
	
	Options:
	  -h, --help
		show this help message and exit
	  -s SEEDS, --seeds=SEEDS
		the web sites from which to start crawling
	  -d DOWNLOADERS, --download=DOWNLOADERS
		number of threads which download web pages
	  -p PARSERS, --parser=PARSERS
		number of threads which parse web pages to extract links

	
###Desgin:###
	
	# Engine
		The main component of a crawler. The job of an engine consists of:
		-- initializes two queues: urlQ storing urls, pageQ storing downloaded web pages.
		-- starts/stops the configured number of downloader threads and parser threads.
	
	# Downloader
		Downloader keeps fetching url from the urlQ and downloading web pages located that url only if the url hasn't been visited before.
		Everytime a pages is downloaded, it will be put into the pageQ for parsing.
	
	# Parser
		Parser keeps fetching page from pageQ and exacting links by parsing the html tags.
		All the extracted links will be put into the urlQ for downloading.
	
	
