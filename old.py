class Node(object):
	"""represents an entry in data.csv that will be used to train our neural network"""
	def __init__(self, ticker, domain, url):
		# self.query	= query		#
		self.ticker = ticker 	# string
		self.domain = domain 	# string
		self.sector = ''		# string
		self.industry = ''		# string
		self.article = '' 		# string
		self.url = url 			# string
		self.date = None		# datetime.date
		self.sentences = []		# array (string)
		self.words = []			# array (string)
		self.price_init = 0.0	# float
		self.price_t1 = 0.0		# float
		self.price_t2 = 0.0		# float
		self.price_t3 = 0.0		# float
		self.price_t4 = 0.0		# float
		self.price_t5 = 0.0		# float

		self.set_params()
		#logger.debug(self.sector, self.industry)

	def set_params(self):
		try:
			xml = parse(urlopen('http://www.google.com/finance?&q='+self.ticker))
  			self.sector = xml.xpath("//a[@id='sector']")[0].text
  			self.industry = xml.xpath("//a[@id='sector']")[0].getnext().text
  		except:
  			logger.error('set params error')

	def set_sentences(self, article):
		self.sentences = sent_tokenize(article)

	def set_words(self, article):
		W = word_tokenize(article)
		self.words = [w for w in W if len(w) > 1]

	def dictify(self):
		return {	'ticker': self.ticker,
					'sector': self.sector,
					'industry': self.industry,
					'domain': self.domain,
					'article': self.article,
					'url': self.url,
					'date': self.date,
					'sentences': self.sentences,
					'words': self.words,
					'priceInit': self.price_init,
					'priceT1': self.price_t1 
				}

	#def set_prices(self):


# ------------------------------------
#
# WEB SCRAPING METHODS 
#
# ------------------------------------


# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

def check_url(url, source):
	'''
	ensure the url begins with http && is from the source
	'''
	valid_schemes = ['http', 'https']
	url_obj = urlparse(link)
	return (url_obj.scheme in valid_schemes) and (url_obj.hostname.split('.')[1].upper() == source.upper())

def root_path(path):
	while path.dirname(path) != '/':
		path = path.dirname(path)
	return path[1:]

# url = "https://www.bloomberg.com/politics/articles/2017-04-09/melenchon-fillon-tap-momentum-in-quest-of-french-election-upset"
# print root_path(urlparse(url).path)

def find_title(soup):
	'''
	returns the content from the BS4 object if a title tag exists,
	else returns an empty string 
	'''
	title = soup.find("title").contents
	if len(title) > 0:
		return title[0]
	return ""

def _date(date):
	return date['datetime'].strip('\n')

def _article_timestamp(date):
	return date['datetime'].strip('\n')

def find_date(soup):
	'''
	takes in a beautiful soup object and finds the date field
	gets the date value and format dates as %Y-%m-%d %H:%M:%S
	returns a datetime object of this date
	'''
	IDs = ['date','article-timestamp']

	for ID in IDs:
		date = soup.find(class_= ID)
		if date != None:
			currID = ID
			break

	if date == None: return None 

	options = {
		'date':  _date,
		'article-timestamp': _article_timestamp, 
	}

	if currID in options.keys():
		try:  
			return dparser.parse(options[currID](date), fuzzy=True)
		except:
			pass
	return None 

def cname_formatter(cName):
	replace_dict = {'Corporation': ' ', ',': ' ', 'Inc.': ' '} #	to improve query relavence 
	robj = re.compile('|'.join(replace_dict.keys())) 
	return robj.sub(lambda m: replace_dict[m.group(0)], cName) #	returns bare company name

def get_name(symbol):
	"""
	Convert the ticker to the associated company name
	"""
	url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
	result = requests.get(url).json()

	for x in result['ResultSet']['Result']:
		if x['symbol'] == symbol:
			return x['name']

# def bloomberg_parser(soup):

def parse_article(soup, domain):
	'''
	takes in a BS4 object that represents an article embedded in HTML
	returns the article body as a string 
	Currently optimized for: Bloomberg, SeekingAlpha
	'''
	specialized = ['BLOOMBERG']
	if not domain in specialized:
		domain = 'DEFAULT'
	p_offset = {
		'BLOOMBERG': 8,
		'DEFAULT':	 0,
	}
	export_html = ""
	p_tags = soup.find_all('p')
	pre_tags = soup.find_all('pre')
	data = p_tags[p_offset[domain]:] + pre_tags

	#cleantext = BeautifulSoup(raw_html).text

	for i in data:
		try:
			export_html += i.contents[0]
		except:
			pass

	# check_relavence(html)
	return export_html

def _scrape_link(link, ticker):

	if not check_url(link):
		logger.error('invalid url')
		return -1

	#	OPEN PAGE AND GET THE HTML
	req = urllib2.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
	try:
		page = urllib2.urlopen(req)
	except:
		logger.error('urllib2 open error')
		return -1
	soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), "html.parser")

	#	PICK APART THE SOUP OBJECT
	# root_path = root_path(url_obj.path)
	title = find_title(soup)
	date = find_date(soup)

	n = Node(ticker=ticker, domain=domain, url=link)		#	if we got here, we have successfully parsed the article 
	n.date = date
	n.title = title
	result = parse_article(soup, domain.upper())

	if result < 0:
		return result

	n.article = result
	return n

def scrape_link(link, ticker):
	result = _scrape_link(link, ticker)

	options = {						#	possible error conditions
		-1: "ERROR -- bad url",	
	}

	if result in options.keys():
		# logger.warn("Error parsing article %s" % options[result])
		return None		#	there was an error

	return result 					#	successful, return a Node object 



# 	-----------------
#
#	HELPER FUNCTIONS
#
#	-----------------

def check_url(url):
	'''
	ensure the url begins with http
	'''
	valid_schemes = ['http', 'https']
	if (urlparse(url).scheme) in valid_schemes:
		return 1
	return -1

def root_path(path):
	while path.dirname(path) != '/':
		path = path.dirname(path)
	return path[1:]

# url = "https://www.bloomberg.com/politics/articles/2017-04-09/melenchon-fillon-tap-momentum-in-quest-of-french-election-upset"
# print root_path(urlparse(url).path)

def find_date(soup):
	'''
	returns the content from the BS4 object if a title tag exists,
	else returns an empty string 
	'''
	title = soup.find("title").contents
	if len(title) > 0:
		return title[0]
	return ""

def _date(date):
	return datetime.strptime(date.contents[0].strip('\n'), "%Y-%m-%dT%H:%M:%SZ")

def _article_timestamp(date):
	return datetime.strptime(date['datetime'].strip('\n'), "%Y-%m-%dT%H:%M:%S.%fZ")


def find_date(soup):
	'''
	takes in a beautiful soup object and finds the date field
	gets the date value and format dates as %Y-%m-%d %H:%M:%S
	returns a datetime object of this date
	'''
	IDs = ['date','article-timestamp']

	for ID in IDs:
		date = soup.find(class_= ID)
		if date != None:
			currID = ID
			break

	if date == None: return None 

	options = {
		'date': _date,
		'article-timestamp': _article_timestamp,
	}

	if currID in options.keys():
		return options[currID](date)
	return None 

def cname_formatter(cName):
	replace_dict = {'Corporation': ' ', ',': ' ', 'Inc.': ' '} #	to improve query relavence 
	robj = re.compile('|'.join(replace_dict.keys())) 
	return robj.sub(lambda m: replace_dict[m.group(0)], cName) #	returns bare company name
	

def get_name(symbol):
	"""
	Convert the ticker to the associated company name
	"""
	url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
	result = requests.get(url).json()
	
	for x in result['ResultSet']['Result']:
		if x['symbol'] == symbol:
			return x['name']

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f seconds' % (f.func_name, (time2-time1))
        return ret
    return wrap


#	--------------------------------------	
#	
# 	DATA AGGREGATION AND PARSING FUNCTIONS
#
#	--------------------------------------

# def bloomberg_parser(soup):

def parse_article(soup, domain):
	'''
	takes in a BS4 object that represents an article embedded in HTML
	returns the article body as a string 
	Currently optimized for: Bloomberg, SeekingAlpha
	'''
	p_offset = {
		'BLOOMBERG': 8,
		'DEFAULT':	 0,
	}
	export_html = ""
	p_tags = soup.find_all('p')
	pre_tags = soup.find_all('pre')
	data = p_tags[p_offset[domain]:] + pre_tags

	for i in data:
		export_html += i.contents[0]

	# check_relavence(html)
	return export_html


def _scrape_url(url):
	'''
	helper function for scrape_url
	''' 
	if check_url(url) < 0:
		return -1

	#	OPEN PAGE AND GET THE HTML
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	try:
		page = urllib2.urlopen(req)
	except urllib2.HTTPError, urllib2.URLError:
		return -1
	soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), "html.parser")

	#	PICK APART THE SOUP OBJECT
	url_obj = urlparse(url)
	domain = url_obj.hostname.split('.')[1]
	root_path = root_path(url_obj.path)
	title = find_date(soup)
	date = find_date(soup)
	result = parse_article(soup, domain.upper())

	if result < 0:
		return result

	# STORE ALL INFORMATION IN A NODE 
	return None
	# return Node(title, date, article)		#	if we got here, we have successfully parsed the article 

def scrape_url(url):
	'''
	takes in a ticker and a url and returns the article body as a string 
	as well as the associated change in stock price 
	'''
	result = _scrape_url(url)

	options = {						#	possible error conditions
		-1: "ERROR -- bad url",	
	}

	if result in options.keys():
		return options[result]		#	there was an error, return it 

	return result 					#	successful, return a Node object 

# scrape_url('https://www.bloomberg.com/press-releases/2017-04-13/under-armour-announces-nomination-of-jerri-l-devard-to-board-of-directors')
# scrape_url('https://www.bloomberg.com/news/articles/2017-02-10/now-under-armour-has-a-trump-problem-too')
# scrape_url('https://www.bloomberg.com/news/articles/2017-01-31/under-armour-admits-it-s-still-not-cool-enough')

def _parse_google(query):
	"""
	Get the URLs from the Google result page for the given query using Beautiful Soup

	@type  query: Query
    @param queries: a Query to get Google Page

	@rtype:  list
	@return: array of URLS for the given Query

	@raise IOError: An exception is raised on error.
	@raise urllib2.URLError: An exception is raised on error.
	@raise urllib2.HTTPError: An exception is raised on error.
	"""
	q = query.source + "+" + query.ticker + "+articles"
	html = "https://www.google.co.in/search?site=&source=hp&q="+q+"&gws_rd=ssl"
	req = urllib2.Request(html, headers={'User-Agent': 'Mozilla/5.0'})
	try:
		soup = BeautifulSoup(urllib2.urlopen(req).read(),"html.parser")
	except (urllib2.HTTPError, urllib2.URLError) as e:
		print "error ", e 
		return []

	#Re to find URLS
	reg=re.compile(".*&sa=")

	#get all web urls from google search result 
	links = []
	for item in soup.find_all(attrs={'class' : 'g'}):
		link = (reg.match(item.a['href'][7:]).group())
	   	link = link[:-4]
	   	links.append(link)
	return links



def get_urls(Nodes):
	"""
	takes in a list of queries and returns a list of urls derived from the queries 

	@type  queries: list
    @param queries: list of Query objects to search for

	@rtype:  list
	@return: array of URLS for the given Queries
	"""
	total_links = []
	for query in queries:
		local_links = list()
		if logger:
			logging_path = os.path.abspath(os.path.join(__file__ ,"../../..")) + '/static/logs/'
			path = logging_path + query.ticker + '.txt'
			if not os.path.isfile(path):
				file_w = open(path, 'w')
				print "writing new log file"
			else:
				file = open(path, 'r')
				local_links = file.readlines()
				local_links = [link.rstrip() for link in local_links]
				file.close()
				file_w = open(path, 'a')
				print "appeneding to log file"

		print "getting URLS for ", query.ticker
		links_found = _parse_google(query)
		links_new 	= [link for link in links_found if link not in local_links]
		if logger:
			for link in links_new:
				print "writing: ", link
				file_w.write(link+'\n')
		total_links += links_new
	return total_links


def create_nodes(ticker_arr, source_arr):
