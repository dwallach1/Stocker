#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from __future__ import unicode_literals, print_function
import re, logging, time
from urlparse import urlparse
from collections import namedtuple, defaultdict
import requests
from datetime import datetime, timedelta, tzinfo
from pytz import timezone
import pytz
import dateutil.parser as dateparser
import numpy as np
from bs4 import BeautifulSoup 
import dryscrape

logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.DEBUG)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)

GOOGLE_WAIT = 20 
PriceChange = namedtuple('PriceChange', 'status magnitude')

class RequestHandler():
	"""handles making HTTP requests using request library"""
	def get(self, url):
		
		#headers = {'User-Agent': 'Mozilla/5.0'}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4'}
		try:
			req = requests.get(url, headers=headers)
			if req.status_code == 503:
				logger.warn('Request code of 503')
				time.sleep(GOOGLE_WAIT)
				req = requests.get(url, headers=headers)
		except requests.exceptions.RequestException as e:
			logger.error('RequestHandler GET Error: {}'.format(str(e)))
			return None
		else: return req

class WebNode(object):
	"""represents an entry in data.csv that will be used to train the sentiment classifier"""
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
      			setattr(self, key, value)
	
	def __iter__(self):
    		attrs = [attr for attr in dir(self) if attr[:2] != '__']
    		for attr in attrs:
      			yield attr, getattr(self, attr)

def scrape(url, source, ticker=None, min_length=30, **kwargs):
	"""
	main parser function, initalizes WebNode and fills in the data
	returns -> WebNode | list on success, None on error 
	:param url: url to parse
	:type url: string
	:param souce: the source provided in the query
	:type source: string
	:param ticker: a stock ticker, used to find more specific information
	:type ticker: string
	:param min_length: the minimum amount of words if length_checker is set to true
	:type min_length: int
	"""
	source = source.lower()

	flags = defaultdict(lambda: False)
	for param in kwargs:
		flags[param] = kwargs[param]

	url_obj = urlparse(url)
	if not url_obj: 
		logger.warn('url_obj unable to parse url')
		return None
	if not validate_url(url_obj, source, curious=flags['curious']): 
		logger.warn('validate_url returned false')
		return None

	# ONLY if needed: visit page and triggger JS -> capture html output as Soup object
	# session = dryscrape.Session()
	# session.visit(url)
	# response = session.body()
	# soup = BeautifulSoup(response, 'html.parser')

	response = RequestHandler().get(url)
	if response == None or response.status_code == 404: 
		logger.warn('Error getting content for {} -- NULL response or 404 status'.format(url))
		return None
	soup = BeautifulSoup(response.text, 'html.parser')
	
	# check url args
	path = url_path(url_obj, source)
	if path in homepages(): return crawl_home_page(soup, path, source)

   	# search for publishing date
   	wn_args = {'url':url}
	pubdate = find_date(soup, source, path)
	if pubdate == None and flags['date_checker']: 
		logger.warn('publishing date flag checked and not able to parse date from html')
		return None
	wn_args['pubdate'] = pubdate

	# search for article
	article = find_article(soup, source, path)
	wn_args['article'] = article
	logger.debug('found article with length: {}'.format(len(article)))

	# check words
	if flags['length_checker'] and len(article.decode('utf-8').split(' ')) < min_length: 
		logger.warn('length_checker flag checked and article did not meet standards')
		return None
	
	# handle indutry/sector parsing
	if (flags['find_industry'] or flags['find_sector']) and ticker:
		industry, sector = get_sector_industry(ticker)
		if flags['find_industry']: 	wn_args['industry'] = industry
		if flags['find_sector']: 	wn_args['sector'] = sector

	# handle classification process
	if flags['classification'] and ticker and pubdate != None:	
		class_ = classify(pubdate, ticker, offset=flags['offset'], squeeze=flags['squeeze'])
		wn_args['classification'] = class_.status
		if flags['magnitude']: wn_args['magnitude'] = class_.magnitude

	return WebNode(**wn_args)

def url_path(url_obj, source):
	length = defaultdict(lambda: 1)
	length['msn'] = 2
	length['zacks'] = 2
	paths = url_obj.path.split('/')[1:] # first entry is '' so exclude it
	return '+'.join(paths[:length[source]]).lower()

def homepages(): return ['quote', 'symbol', 'finance', 'markets', 'investing', 'en-us+money']

def validate_url(url_obj, source, curious=False):
	"""
	basic url checking to save overhead
	returns -> boolean
	:param url_obj: the url in question
	:type url_obj: urlparse object
	:param souce: the source provided in the query
	:type source: string
	:param curious: determines if the function should check to see if the domain matches the source
	:type curious: boolean
	"""
	valid_schemes = ['http', 'https']
	if not url_obj.hostname: return False
	return (url_obj.scheme in valid_schemes) and ((url_obj.hostname == source_translation(source)) or curious)

def get_sector_industry(ticker):
	"""
	looks for the associated sector and industry of the stock ticker
	returns -> two strings (first: industry, second: sector)
	:param ticker: associated stock ticker to look up for the information
	:type ticker: string
	"""
	industry, sector = '', ''
	google_url = 'https://www.google.com/finance?&q='+ticker
	req = RequestHandler().get(google_url)
	if req == None: return WebNode(url, pubdate, article, words, sentences, industry, sector)
	
	s = BeautifulSoup(req.text, 'html.parser')
	container = s.find_all('a')
	next_ = False
	for a in container:
		if next_: 
			industry = a.text.strip()
			break
		if a.get('id') == 'sector': 
			sector = a.text.strip()
			next_ = True
	return industry, sector

def find_date(soup, source, container):
	"""
	parses a beautifulsoup object in search of a publishing date
	returns -> datetime on success, None on error
	:param soup: a beautifulsoup object
	:param source: the source provided in the query
	:type source: string
	:param container: an html attribute to where dates are stored for valid sources
	:type container: string
	"""
	tz = timezone('US/Eastern')
	tz_utc = pytz.utc
	now = datetime.now()

	key = '+'.join([source,container])

	print ('key is {}'.format(key))
	print ('ayy {}'.format('investorplace+'+str(now.year)))
	container = {
		'bloomberg+press-releases': soup.find('span', attrs={'class': 'date'}),
		'bloomberg+news':			soup.find('time', attrs={'itemprop': 'datePublished'}),
		'seekingalpha+article':		soup.find('time', attrs={'itemprop': 'datePublished'}),
		'reuters+article':			soup.find('div', attrs={'class': 'ArticleHeader_date_V9eGk'}),
		'investopedia+news':		soup.find('span', attrs={'class':'by-author'}),
		'thestreet+story':			soup.find('time', attrs={'itemprop':'datePublished'}),
		'yahoofinance+news': 		soup.find('time', attrs={'itemprop':'datePublished'}),
		'marketwatch+story': 		soup.find('p', attrs={'id': 'published-timestamp'}),
		'msn+en-us+news':			soup.find('time'),
		'barrons+articles':			soup.find('meta', attrs={'itemprop': 'datePublished'}),
		'investorplace+'+str(now.year): soup.find('span', attrs={'class': 'entry-date'}),
		'benzinga+general':			soup.find('div', attrs={'class': 'article-date-wrap'})
	}

	keys = container.keys()
	if key not in keys: return None
	date_html = container[key]
	if date_html == None: return None

	if 	 key == 'bloomberg+press-releases': return dateparser.parse(date_html.text.strip(), fuzzy=True).astimezone(tz)
	elif key == 'bloomberg+news':		 	return dateparser.parse(date_html['datetime'], fuzzy=True).astimezone(tz)
	elif key ==	'seekingalpha+article':		return dateparser.parse(date_html['content'], fuzzy=True).astimezone(tz)
	elif key ==	'reuters+article':			return tz_utc.localize(dateparser.parse(''.join(date_html.text.strip().split('/')[:2]), fuzzy=True)).astimezone(tz)
	elif key ==	'investopedia+news':		return dateparser.parse(date_html.text.strip(), fuzzy=True)
	elif key == 'thestreet+story':			return dateparser.parse(date_html['datetime'], fuzzy=True)
	elif key == 'yahoofinance+news':		return dateparser.parse(date_html['datetime'], fuzzy=True).astimezone(tz)
	elif key == 'marketwatch+story':		return dateparser.parse(date_html.text.strip(), fuzzy=True)
	elif key == 'msn+en-us+news':			return dateparser.parse(date_html['datetime'], fuzzy=True).astimezone(tz)
	elif key == 'barrons+articles':			return dateparser.parse(date_html['content'], fuzzy=True).astimezone(tz)
	elif key == 'investorplace+'+str(now.year): return tz.localize(dateparser.parse(date_html.text.strip(), fuzzy=True))
	elif key == 'benzinga+general': 		return tz.localize(dateparser.parse(date_html.text.strip(), fuzzy=True))
	return None

def find_article(soup, source, container):
	"""
	parses a beautifulsoup object in search of the url's content (the article)
	returns -> string
	:param soup: a beautifulsoup object
	:param source: the source provided in the query
	:type source: string
	:param container: an html attribute to where dates are stored for valid sources
	:type container: string
	"""
	key = '+'.join([source, container])
	offset = 	defaultdict(lambda: 0)
	tag = 		defaultdict(lambda: 'p')
	offset['bloomberg+news'] = 8
	tag['bloomberg+press-releases'] = 'pre'
	return ' '.join(map(lambda p: p.text.strip(), soup.find_all(tag[key])[offset[key]:])).encode('utf-8')

def crawl_home_page(soup, ID, source):
	"""
	looks for links of a domain's ticker homepage
	returns -> list on success, None on error
	:param soup: a beautifulsoup object
	:param ID: the url path to indicate how to parse the soup object
	:type ID: string
	"""
	dryscrapes = ['yahoofinance', 'thestreet', 'investopedia']
	find = source in ['reuters', 'investopedia', 'marketwatch', 'msn', 'wsj', 'barrons']
	dry = source in dryscrapes
	soups = {
		'bloomberg': 		soup.find_all('a', attrs={'class': 'news-story__url'}, href=True),
		'thestreet': 		soup.find_all('a', attrs={'class': 'news-list-compact__object-wrap'}, href=True), 
		'seekingalpha':		soup.find_all('a', attrs={'sasource': 'qp_latest'}, href=True),
		'reuters':			soup.find('div', attrs={'id': 'companyOverviewNews'}),
		'investopedia': 	soup.find('section', attrs={'id':'News'}),
		'marketwatch':		soup.find('div', attrs={'class': 'j-tabPanes'}),
		'msn':				soup.find('div', attrs={'class': 'financebingnewstemplate'})
		# 'barrons': 			soup.find('div', attrs={'class': 'row row--news'}
		# 'wsj':			soup.find('ul', attrs={'class': 'cr_newsSummary'})
	}

	bases = {
		'thestreet': 		'https://www.thestreet.com',
		'seekingalpha':		'https://seekingalpha.com',
		'reuters':			'http://reuters.com',
		'investopedia': 	'http://investopedia.com',
		'bloomberg':		'',
		'marketwatch': 		'',
		'msn':				'https://www.msn.com'
		# 'barrons':			''
	}

	if find and not dry: return [bases[source] + url['href'] for url in soups[source].find_all('a')]
	if not (source in soups.keys()) or dry: return None
	return [bases[source] + url['href'] for url in soups[source]]
	
def classify(pubdate, ticker, interval=20, offset=10, squeeze=False):
	"""
	finds an associated classification based on the stock price fluctiation of the given ticker
	returns -> StockChange  {-1000: not_found, -1.0: declined, 0.0: stayed the same, 1.0:increeased}
	:param pubdate: the publishing date of the article
	:type pubdate: datetime object
	:param ticker: the stock ticker to search the API for
	:type ticker: string
	:param offset: the amount of days to search for the date from the API
	:type offset: int
	:param offset: the interval to for stock price change (stockprice[pubdate+offset(minutes)] - stockprice[pubdate])
	:type offset: int
	"""
	not_found = PriceChange(-1000, 0)
	
	today, pubdate = datetime.today().replace(tzinfo=None), pubdate.replace(tzinfo=None)
	margin = timedelta(days = interval) 
	if ((today - margin) > pubdate): return not_found

	url = 'https://www.google.com/finance/getprices?i=60&p={}d&f=d,o,h,l,c,v&df=cpct&q={}'.format(interval, ticker.upper())
	req = RequestHandler().get(url)
	if req.content == None: return not_found

	source_code = req.content
	split_source = source_code.split('\n')
	headers = split_source[:7] 
	stock_data = split_source[7:]
	if len(split_source) < 8: return not_found

	dates, close_ = [], []
	curr_date = None
	for line in stock_data[:-1]:
		l = line.split(',')
		# date, close, high, low, openp, volume = l[0], l[1], l[2], l[3], l[4], l[5]
		date, close = l[0], l[1]
		if date[0] == 'a':
			curr_date = str2date(date[1:])
			dates.append(curr_date)
			close_.append(close)
		else: 
			dates.append(curr_date + timedelta(minutes=int(date)))
			close_.append(float(close))

	bitmap =  [same_date(date, pubdate) for date in dates] # assume publishing date is in EST time
	bitsum = sum(bitmap) 
	if bitsum == 0: bitsum = sum(same_date(timestamp, pubdate+timedelta(hours=3)) for timestamp in dates) # possibly date was in PDT time
	if bitsum > 1: return not_found  # this is an error case
	try:		idx = bitmap.index(1)
	except:		return not_found

	now = datetime.now()
	market_close = datetime(year=now.year, month=now.month, day=now.day, hour=15, minute=58) # market closes at 4 -- last record at 3:58
	diff = (market_close - dates[idx].replace(tzinfo=None)).seconds / 60
	if pre_mrkt_close((dates[idx] + timedelta(minutes=offset)), market_close): 
		chng = float(close_[idx+offset] - close_[idx])
		return PriceChange(np.sign(chng), abs(float(chng)))
	elif diff > 0 and squeeze: 	
		chng = close_[idx+diff] - close_[idx]
		return PriceChange(np.sign(chng), abs(float(chng)))
	else: return not_found
	
def same_date(date1, date2):
	"""
	checks if two dates are equal (if one or both is not a valid datetime)
	returns -> int in the set {0,1}
	:param date(1/2): datetime | time object
	"""
	if (date1.year == date2.year) and (date1.month == date2.month) and (date1.day == date2.day) and (date1.hour == date2.hour) and (date1.minute == date2.minute): return 1
	return 0

def pre_mrkt_close(date, mrkt_close):
	"""
	checks if a given date is before the market close (just need to check hour/minute params)
	returns -> boolean
	:param date: the date in question
	:type date: datetime object
	:param mrkt_close: when the stock market closes
	:type mrkt_close: datetime object
	"""
	if date.hour < mrkt_close.hour: return True
	elif date.minute < mrkt_close.minute: return True
	return False

def str2date(datestr):
	"""
	converts a string date to a unix timestamp 
	returns -> datetime object
	:param datestr: raw representation of date from API
	:type datestr: string
	"""
	return datetime.fromtimestamp(int(datestr), timezone('US/Eastern'))	 

def source_translation(name, host=True):
	"""
	finds a correlating hostname or source for a name input
	returns -> string on success, None on error
	:param name: the full host name or the source name
	:type name: string
	:param host: tells which dict to use 
	:type host: boolean
	"""
	hosts = {
		'motleyfool': 	'www.fool.com',
		'bloomberg': 	'www.bloomberg.com',
		'seekingalpha': 'seekingalpha.com',
		'yahoofinance': 'finance.yahoo.com',
		'investopedia': 'www.investopedia.com',
		'investing':	'www.investing.com',
		'marketwatch': 	'www.marketwatch.com',
		'googlefinance': 'www.google.com',
		'reuters': 		'www.reuters.com',
		'thestreet': 	'www.thestreet.com',
		'msn':			'www.msn.com',
		'wsj':			'www.wsj.com',
		'barrons':		'www.barrons.com',
		'zacks':		'www.zacks.com',
		'investorplace':'investorplace.com',
		'benzinga':		'www.benzinga.com'

	}
	sources = {v: k for k, v in hosts.iteritems()}
	#inv_map = {v: k for k, v in my_map.items()} python 3+ --> use when we upgrade
	bucket = hosts if host else sources 
	if not (name in bucket.keys()): return None
	return bucket[name.lower()]

