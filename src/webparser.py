from __future__ import unicode_literals, print_function
import re, logging, time
from urlparse import urlparse
from collections import namedtuple, defaultdict
import requests
from datetime import datetime, timedelta
from pytz import timezone
import dateutil.parser as dateparser
import numpy as np
from bs4 import BeautifulSoup 
import dryscrape

logger = logging.getLogger(__name__)
GOOGLE_WAIT = 20
PriceChange = namedtuple('PriceChange', 'status magnitude')

class RequestHandler():
	"""handles making HTTP requests using request library"""
	def get(self, url):
		headers = {'User-Agent': 'Mozilla/5.0'}
		try:
			req = requests.get(url, headers=headers)
			if req.status_code == 503:
				logger.warn('Request code of 503')
				time.sleep(GOOGLE_WAIT)
				req = requests.get(url, headers=headers)
			return req
		except requests.exceptions.RequestException as e:
			logger.error('RequestHandler GET Error: {}'.format(str(e)))
			return None

class WebNode(object):
	"""represents an entry in data.csv that will be used to train the sentiment classifier"""
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
      			setattr(self, key, value)
	
	def __iter__(self):
    		attrs = [attr for attr in dir(self) if attr[:2] != '__']
    		for attr in attrs:
      			yield attr, getattr(self, attr)

def homepages(): return ['quote', 'symbol', 'finance', 'markets']

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
	flags = defaultdict(lambda: False)
	for param in kwargs:
		flags[param] = kwargs[param]

	url_obj = urlparse(url)
	if not url_obj: return None
	if not validate_url(url_obj, source, curious=flags['curious']): return None

	# ONLY if needed: visit page and triggger JS -> capture html output as Soup object
	# session = dryscrape.Session()
	# session.visit(url)
	# response = session.body()
	response = RequestHandler().get(url)
	if response == None: return None
	soup = BeautifulSoup(response.text, 'html.parser')
	# soup = BeautifulSoup(response, 'html.parser')

	# check url args
	paths = url_obj.path.split('/')[1:] # first entry is '' so exclude it
	p = paths[0].lower()
	if p in homepages(): return crawl_home_page(soup, p)
   	
   	# search for publishing date
   	wn_args = {'url':url}
	pubdate = find_date(soup, source, paths[0])
	if pubdate is None and flags['date_checker']: return None
	wn_args['pubdate'] = pubdate

	# search for article
	article = find_article(soup, source, paths[0])
	logger.info('found pubdate to be: {}'.format(str(pubdate)))
	wn_args['article'] = article

	# check words
	if flags['length_checker'] and len(article.decode('utf-8').split(' ')) < min_length: return None
	
	# handle indutry/sector parsing
	if (flags['find_industry'] or flags['find_sector']) and ticker:
		industry, sector = get_sector_industry(ticker)
		if flags['find_industry']: 	wn_args['industry'] = industry
		if flags['find_sector']: 	wn_args['sector'] = sector


	if flags['classification'] and ticker:	
		class_ = classify(pubdate, ticker)
		wn_args['classification'] = class_.status
		if flags['magnitude']: wn_args['magnitude'] = class_.magnitude

	return WebNode(**wn_args)

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
	domain_list = [x for x in url_obj.hostname.split('.') if len(x) > 3]
	domain = ''
	if len(domain_list) > 0: domain = domain_list[0].lower()
	return (url_obj.scheme in valid_schemes) and ((domain == source.lower()) or curious)

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
	s, c = source.lower(), container.lower()
	try:
		if s == 'bloomberg':
			if c == 'press-releases':
				date_html =  soup.find('span', attrs={'class': 'pubdate'})
				if not (date_html is None): return dateparser.parse(date_html.text.strip(), fuzzy=True)
			date_html = soup.find('time')
			if not (date_html is None): return dateparser.parse(date_html.text.strip(), fuzzy=True)
		elif s == 'seekingalpha':
			if c == 'filing': return None
			date_html = soup.find('time', attrs={'itemprop': 'datePublished'})
			if not (date_html is None): return dateparser.parse(date_html['content'], fuzzy=True)
		elif s == 'reuters':
			date_html = soup.find('div', attrs={'class': 'ArticleHeader_date_V9eGk'})
			if not (date_html is None): return dateparser.parse(''.join(date_html.text.strip().split('/')[:2]), fuzzy=True)
		elif s == 'investopedia':
			date_html = soup.find('span', attrs={'class':'by-author'})
			if not (date_html is None): return dateparser.parse(date_html.text.strip(), fuzzy=True)
		elif s == 'thestreet':
			date_html = soup.find('time', attrs={'itemprop':'datePublished'})
			if not (date_html is None): return dateparser.parse(date_html['datetime'], fuzzy=True)
		
		# TODO: module not specialized in source + need to account for errors
		# try:
		# except:
		return None
	except: return None

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
	s, c = source.lower(), container.lower()
	offset = 0 
	if s == 'bloomberg': offset = 8
	return ' '.join(list(map(lambda p: p.text.strip(), soup.find_all('p')[offset:]))).encode('utf-8')

def crawl_home_page(soup, ID):
	"""
	looks for links of a domain's ticker homepage
	returns -> list on success, None on error
	:param soup: a beautifulsoup object
	:param ID: the url path to indicate how to parse the soup object
	:type ID: string
	"""
	if ID == 'quote':       # bloomberg / thestreet
		urls = soup.find_all('a', attrs={'class': 'news-story__url'}, href=True)
		if not (urls == None): return [url['href'] for url in urls]
		urls = soup.find_all('a', attrs={'class': 'news-list-compact__object-wrap'}, href=True) 
		base = 'https://www.thestreet.com'
		if not (urls == None): return [base + url['href'] for url in urls]
	elif ID == 'symbol':  # seeking alpha
		base = 'https://seekingalpha.com'
		urls = soup.find_all('a', attrs={'sasource': 'qp_latest'}, href=True)
		if not (urls == None): return [base + url['href'] for url in urls]
	elif ID == 'finance':   # reuters
		base = 'http://reuters.com'
		urls = soup.find('div', attrs={'id': 'companyOverviewNews'})
		if not (urls == None): return [base + url['href'] for url in urls.find_all('a')]
	elif ID == 'markets':   # investopedia
		base = 'http://investopedia.com'
		urls = soup.find('section', attrs={'id':'News'})
		if not (urls == None): return [base + url['href'] for url in urls.find_all('a')]
	return None

def classify(pubdate, ticker, offset=10):
	"""
	finds an associated classification based on the stock price fluctiation of the given ticker
	returns -> StockChange  {-1000: not_found, -1.0: declined, 0.0: stayed the same, 1.0:increeased}
	:param pubdate: the publishing date of the article
	:type pubdate: datetime object
	:param ticker: the stock ticker to search the API for
	:type ticker: string
	:param offset: the interval to for stock price change (stockprice[pubdate+offset(minutes)] - stockprice[pubdate])
	:type offset: int
	"""
	not_found = PriceChange(-1000, 0)
	
	today = datetime.today()
	today, pubdate = today.replace(tzinfo=None), pubdate.replace(tzinfo=None)
	margin = timedelta(days = 20) 
	if ((today - margin) > pubdate): return not_found

	url = 'https://www.google.com/finance/getprices?i=60&p=20d&f=d,o,h,l,c,v&df=cpct&q={}'.format(ticker.upper())
	req = RequestHandler().get(url)
	if req.content == None: return not_found

	source_code = req.content
	split_source = source_code.split('\n')
	headers = split_source[:7] 
	stock_data = split_source[7:]

	if len(split_source) < 8: return not_found

	dates, highp, lowp, open_, close_ = [], [], [], [], []
	curr_date = None
	for line in stock_data[:-1]:
		l = line.split(',')
		date, close, high, low, openp, volume = l[0], l[1], l[2], l[3], l[4], l[5]
		if date[0] == 'a':
			curr_date = str2unix(date[1:])
			dates.append(curr_date)
		else: 
			dates.append(curr_date + timedelta(minutes=int(date)))
			highp.append(float(high))
			lowp.append(float(low))
			open_.append(float(openp))
			close_.append(float(close))

	bitmap =  [same_date(date, pubdate) for date in dates] # assume publishing date is in EST time
	bitsum = sum(bitmap) 
	if bitsum == 0: bitsum = sum(same_date(timestamp, pubdate+timedelta(hours=3)) for timestamp in dates) # possibly date was in PDT time
	if bitsum > 1: return not_found # this is an error case
	try:		idx = bitmap.index(1) # at this point, we know there is a match
	except:		return not_found
	
	now = datetime.now()
	market_close = datetime(year=now.year, month=now.month, day=now.day, hour=15, minute=58) # market closes at 4 -- last record at 3:58
	diff = (market_close.minute - dates[idx].minute)
	# print ('highs be: {} at time & {} at time+offset'.format(highp[idx], highp[idx+offset]))
	# print ('lows be: {} at time & {} at time+offset'.format(lowp[idx], lowp[idx+offset]))
	# print ('open be: {} at time & {} at time+offset'.format(open_[idx], open_[idx+offset]))
	# print ('close be: {} at time & {} at time+offset'.format(close_[idx], close_[idx+offset]))
	# print ('dates to be: {} at time & {} at time+offset'.format(dates[idx], dates[idx+offset]))

	if pre_mrkt_close((dates[idx] + timedelta(minutes=offset)), market_close): 
		chng = close_[idx+offset] - close_[idx]
		return PriceChange(np.sign(chng), abs(float(chng)))
	# elif diff > 0: 	
	# 	chng = close_[idx+diff] - close_[idx]
	# 	return PriceChange(np.sign(chng), abs(float(chng)))
	else: return not_found
	
def same_date(date1, date2):
	"""
	checks if two dates are equal (if one or both is not a valid datetime)
	returns -> int in the set {0,1}
	:param date(1/2): datetime | time object
	"""
	if (date1.month == date2.month) and (date1.day == date2.day) and (date1.hour == date2.hour) and (date1.minute == date2.minute): return 1
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

def str2unix(datestr):
	"""
	converts a string date to a unix timestamp 
	returns -> datetime object
	:param datestr: raw representation of date from API
	:type datestr: string
	"""
	date_UTC = datetime.fromtimestamp(int(datestr))	#	dates come in Unix time and converted to local 
	date1, date2 = datetime.now(timezone('US/Eastern')), datetime.now()
	rdelta = date1.hour - date2.hour 					#	convert local time to EST (the timezone the data was recorded in)
	return date_UTC + timedelta(hours=rdelta)	

def name2domain(name):
	"""
	finds a correlating domain for a source input
	returns -> string on success, None on error
	:param name: the full source name
	:type name: string
	"""
	domains = {
		'motley fool': 'fool',
		'bloomberg': 'bloomberg',
		'seeking alpha': 'seekingalpha',
		'yahoo finance': 'finance.yahoo'
	}
	if not (name in domains.keys()): return None
	return domains[name.lower()]

def domain2name(domain):
	"""
	finds a correlating (full) source name for a domain input
	returns -> string on success, None on error
	:param domain: the domain name
	:type domain: string
	"""
	names = {
		'fool': 'motley fool',
		'bloomberg': 'bloomberg',
		'seekingalpha': 'seeking alpha',
		'finance.yahoo': 'yahoo finance'
	}
	if not (domain in names.keys()): return None
	return names[domain.lower()]

