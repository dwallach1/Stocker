from __future__ import print_function
"""
datamine.py
Author: David Wallach

- Uses BeautifulSoup for scraping the data from URLs

This Python module has several purposes oriented around mining data from the web.
The functionality is comprised of gathering urls from google quereis and then getting the data from 
those articles such as the article body and publishing date
"""
import os, sys, logging, json
# import urllib2, httplib, requests
import requests
from urlparse import urlparse
import time, csv, re
from bs4 import BeautifulSoup as BS
import xml
from nltk.tokenize import sent_tokenize, word_tokenize
from datetime import datetime 
import dateutil.parser as dparser

logger = logging.getLogger(__name__)

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

class Miner(object):
	"""Miner class manages the work for mining data and writing it to a csv file"""
	def __init__(self, tickers, sources, csv_path, json_path):
		self.tickers = tickers
		self.sources = sources
		self.csv_path = csv_path
		self.json_path = json_path
		self.queries = []

	def build_queries(self):
		for t in self.tickers:
			for s in self.sources:
				q = t + '+' + s + '+' + 'stock+articles'
				self.queries.append([t, s, q])
		logger.debug('built {} queries'.format(len(self.queries)))

	def mine(self):
		total = len(self.queries)
		logger.debug('Creating {} worker(s)'.format(total))
		logger.info('Starting to build and write batches ...')
		for i,q in enumerate(self.queries):			
			worker = Worker(q[0], q[1], q[2])
			worker.configure(self.json_path)
			worker.work()	
			# self.write_csv(worker.nodes)
			self.write_json(worker.links, worker.ticker)	
		print('\nDone.')

	def write_csv(self, nodes):
		node_dict = list(map(lambda n: n.dictify(), list(filter(lambda n: n.date != None , nodes))))
		write_mode = 'a' if os.path.exists(self.csv_path) else 'w'
		with open(self.csv_path, write_mode) as f:
			fieldnames = sorted(node_dict[0].keys()) # sort to ensure they are the same order every time
			print (fieldnames)
			writer = csv.DictWriter(f, fieldnames=fieldnames)
			if write_mode == 'w':
				writer.writeheader()
			writer.writerows(node_dict)

	def write_json(self, links, ticker):
		write_mode = 'r' if os.path.exists(self.json_path) else 'w' 
		t = ticker.upper()
		with open(self.json_path, write_mode) as f:
			data = json.load(f)
		
		# add links to json
		if t in data.keys():
			original = data[t] 
			updated = original + links 
			data.update({t : updated})
		else:
			data.update({t : links})

		#write the updated json
		with open(self.json_path, 'w') as f:
			json.dump(data, f, indent=4)


class Worker(object):
	"""contains the work of the program, filling in the node data so that it can be written to the csv file"""
	def __init__(self, ticker, source, query):
		self.ticker = ticker.upper()	# string
		self.source = source			# string
		self.query = query				# string
		self.links = []					# array (string)
		self.nodes = []					# array (Node())

	def configure(self, json_path):
		with open(json_path, 'r') as f:
			data = json.load(f)
		self.links = data[self.ticker] if self.ticker in data else []
		logger.debug('configuring links with a length of {}'.format(len(self.links)))

	def work(self):
		self.set_links()
		self.build_nodes()

	def set_links(self):
		html = "https://www.google.co.in/search?site=&source=hp&q="+self.query+"&gws_rd=ssl"
		req = urllib2.Request(html, headers={'User-Agent': 'Mozilla/5.0'})
		try:
			soup = BeautifulSoup(urllib2.urlopen(req).read(),"html.parser")
		except (urllib2.HTTPError, urllib2.URLError) as e:
			logger.error("error {} occurred in function set_links".format(e)) 
			return 

		#find URLS
		reg=re.compile(".*&sa=")

		#get all web urls from google search result 
		links = []
		for item in soup.find_all(attrs={'class' : 'g'}):
			link = (reg.match(item.a['href'][7:]).group())
			link = link[:-4]
			links.append(link)

		self.links = list(filter(lambda link: link not in self.links, links))

	def build_nodes(self):
		for link in self.links:
			node = scrape_link(link, self.ticker)	
			if node != None:
				node.set_sentences(node.article)
				node.set_words(node.article)
				logger.debug("words length is {} and sentence length is {}".format(len(node.words), len(node.sentences)))		
				self.nodes.append(node)
		logger.debug("built {} nodes".format(len(self.nodes)))


# ------------------------------------
#
# WEB SCRAPING METHODS 
#
# ------------------------------------


class WebScraper(object):
	def __init__(self, url, ticker, curious=False):
		self.url = url
		self.source = source
		self.ticker = ticker
		self.curious = curious

	def validate_url(self):
		valid_schemes = ['http', 'https']
		url_obj = urlparse(self.url)
		return (url_obj.scheme in valid_schemes) and (url_obj.hostname.split('.')[1].upper() == self.source.upper())

	def scrape(self):
		if self.curious and not self.validate_url(): return None

		try: 
			req = requests.get(url)
			req.raise_for_status()
		except requests.exceptions.Timeout:
			logger.log('Web Scraper Error opening {} due to Timeout'.format(self.url))
		except requests.exceptions.TooManyRedirects:
			logger.log('Web Scraper Error opening {} due to Too many Redirects'.format(self.url))
		except requests.exceptions.RequestException as e:
			logger.log('Web Scraper Error opening {} due to Timeout'.format(str(e)))


		soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), "html.parser")



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
