#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from __future__ import unicode_literals, print_function
import re, logging, time
from urllib.parse import urlparse
from collections import namedtuple, defaultdict
import requests
from datetime import datetime, timedelta, tzinfo
from pytz import timezone
import pytz
import dateutil.parser as dateparser
import numpy as np
from bs4 import BeautifulSoup 
#import dryscrape
import chardet

from RequestService import RequestHandler
from WebService import WebNode

# set logging configurations
logger = logging.getLogger(__name__)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)


# global declarations
GOOGLE_WAIT = 120 
PriceChange = namedtuple('PriceChange', 'status magnitude')


def scrape(url, source, ticker, min_length=30, **kwargs):
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
		logger.warn('url_obj unable to parse url for url {}'.format(url))
		return None
	if not validate_url(url_obj, source, curious=flags['curious']) and flags['validate_url']: 
		logger.warn('validate_url returned false for {}'.format(url))
		return None

	# ONLY if needed: visit page and triggger JS -> capture html output as Soup object
	# session = dryscrape.Session()
	# session.visit(url)
	# response = session.body()
	# soup = BeautifulSoup(response, 'html.parser')

	response, err = RequestHandler().get(url)
	if response == None or response.status_code == 404: 
		logger.warn('Error getting content for {} -- NULL response or 404 status'.format(url))
		return None
	soup = BeautifulSoup(response.text, 'html.parser')
	
	# check url args
	path = url_path(url_obj, source)
	if path in homepages(): return crawl_home_page(soup, path, source)

	wn_args = {	'url': url, 'ticker': ticker, 'source': source }
   	
	# search for publishing date
	pubdate = find_date(soup, source, path)
	if pubdate == None and flags['date_checker']: 
		logger.warn('publishing date flag checked and not able to parse date from html for url {}'.format(url))
		return None
	wn_args['pubdate'] = pubdate

	# search for article
	article = find_article(soup, source, path)
	logger.debug('{} -> article\'s length is {} characters'.format(url, len(article)))
	try: logger.debug('article string encoding is {}'.format(chardet.detect(article)['encoding']))
	except: logger.debug('article string encoding is not detectable')
	
	# replace non-ASCII values with a spce
	article = re.sub(r'[^\x00-\x7F]+',' ', article)
	wn_args['article'] = article
	logger.debug('after cleaning, article has length: {}'.format(len(article)))

	# check words
	if flags['length_checker'] and len(article.decode('utf-8').split(' ')) < min_length: 
		logger.warn('length_checker flag checked and article did not meet standards for url {}'.format(url))
		return None
	
	# handle indutry/sector parsing
	if (flags['find_industry'] or flags['find_sector']) and ticker:
		industry, sector = get_sector_industry(ticker)
		if flags['find_industry']: 	wn_args['industry'] = industry
		if flags['find_sector']: 	wn_args['sector'] = sector

	# handle classification process
	if flags['classification'] and ticker and pubdate != None:	
		classification = classify(pubdate, ticker, offset=flags['offset'], squeeze=flags['squeeze'])
		wn_args['classification'] = classification.status
		if flags['magnitude']: wn_args['magnitude'] = classification.magnitude

	return WebNode(**wn_args)


def homepages(): 
	"""The containers associated to the valid homepages"""
	return ['quote', 'symbol', 'finance', 'markets', 'investing', 'en-us+money']


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
	# temporarily used to prevent error in writing csv 
	# some of these links are breaking the csv writer function -- need to debug
	#if container == 'press-releases': return 'not working rn'
	
	key = '+'.join([source, container])
	offset = 	defaultdict(lambda: 0)
	tag = 		defaultdict(lambda: 'p')
	offset['bloomberg+news'] = 8
	tag['bloomberg+press-releases'] = 'pre'
	article = ' '.join(map(lambda p: p.text.strip(), soup.find_all(tag[key])[offset[key]:])).encode('utf-8', 'ignore')
	if not isinstance(article, str):
		return article.decode()
	return article

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

	if find and not dry:
		try: 
			links = [bases[source] + url['href'] for url in soups[source].find_all('a')]
		except AttributeError:
			logger.warn('Unable to parse homepage for {}'.format(source))
			return None
		else:
			return links 
	if not (source in soups.keys()) or dry: 
		logger.warn('Unable to parse homepage for {}'.format(source))
		return None
	return [bases[source] + url['href'] for url in soups[source]]


# Currently not working due to Google changing their API
# Google & Yahoo Finance have discountinued their intraday mintute stock data APIs	
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



