import re, logging
from urlparse import urlparse
import requests
from datetime import datetime, timedelta
from pytz import timezone
import dateutil.parser as dateparser
import time
import numpy as np
from bs4 import BeautifulSoup as BS

logger = logging.getLogger(__name__)

def homepages(): return ['quote', 'symbol', 'finance', 'markets']

class WebNode(object):
	"""represents an entry in data.csv that will be used to train our neural network"""
	def __init__(self, url, pubdate, article, words, sentences, industry, sector, classification):
		self.url = url              # string
		self.pubdate = pubdate      # datetime
		self.article = article      # article
		self.words = words          # list
		self.sentences = sentences  # list
		self.industry = industry    # string
		self.sector = sector        # string
		self.classification = classification  #int

def validate_url(url_obj, source, curious=False):
	valid_schemes = ['http', 'https']
	if not url_obj.hostname: return False
	domain_list = list(filter(lambda x: len(x) > 3, url_obj.hostname.split('.')))
	domain = ''
	if len(domain_list) > 0: domain = domain_list[0].lower()
	return (url_obj.scheme in valid_schemes) and ((domain == source.lower()) or curious)

def find_date(soup, source, container):
	s, c = source.lower(), container.lower()
	try:
		if s == 'bloomberg':
			if c == 'press-releases':
				date_html =  soup.find('span', attrs={'class': 'pubdate'})
				if not (date_html is None): return dateparser.parse(date_html.text.strip(), fuzzy=True); return None
			date_html = soup.find('time')
			if not (date_html is None): return dateparser.parse(date_html.text.strip(), fuzzy=True); return None
		elif s == 'seekingalpha':
			if c == 'filing': return None
			date_html = soup.find('time', attrs={'itemprop': 'datePublished'})
			if not (date_html is None): return dateparser.parse(date_html['content'], fuzzy=True); return None
		elif s == 'reuters':
			date_html = soup.find('div', attrs={'class': 'ArticleHeader_date_V9eGk'})
			if not (date_html is None): return dateparser.parse(''.join(date_html.text.strip().split('/')[:2]), fuzzy=True); return None
		elif s == 'investopedia':
			date_html = soup.find('span', attrs={'class':'by-author'})
			if not (date_html is None): return dateparser.parse(date_html.text.strip(), fuzzy=True); return None
		elif s == 'thestreet':
			date_html = soup.find('time', attrs={'itemprop':'datePublished'})
			if not (date_html is None): return dateparser.parse(date_html['datetime'], fuzzy=True); return None
		
		# TODO: module not specialized in source + need to account for errors
		# try:
		# except:
		return None
	except: return None

def find_article(soup, source, container):
	s, c = source.lower(), container.lower()
	offset = 0 
	if s == 'bloomberg': offset = 8
	return ' '.join(list(map(lambda p: p.text.strip(), soup.find_all('p')[offset:]))).encode('utf-8')

def crawl_home_page(soup, ID):
	if ID == 'quote':       # bloomberg / thestreet
		urls = soup.find_all('a', attrs={'class': 'news-story__url'}, href=True)
		if not (urls is None): return list(map(lambda url: url['href'], urls))
		urls = soup.find_all('div', attrs={'class': 'news-story__url'}, href=True) 
		if not (urls is None): return list(map(lambda url: url['href'], urls)); return None
	elif ID == 'symbol':  # seeking alpha
		base = 'https://seekingalpha.com'
		urls = soup.find_all('a', attrs={'sasource': 'qp_latest'}, href=True)
		if not (urls is None): return list(map(lambda url: base + url['href'], urls)); return None  
	elif ID == 'finance':   # reuters
		base = 'http://reuters.com'
		urls = soup.find('div', attrs={'id': 'companyOverviewNews'})
		if not (urls is None): return list(map(lambda url: base + url['href'], urls.find_all('a'))); return None
	elif ID == 'markets':   # investopedia
		base = 'http://investopedia.com'
		urls = soup.findAll('section')
		if not (urls is None): return list(map(lambda url: base + url['href'], urls.find_all('a'))); return None
	return None

def scrape(url, source, curious=False, ticker=None, date_checker=True, length_checker=False, min_length=30, crawl_page=False):
	'''
	parses the url for 
	:param url: a web url
	:type url: string
	:param source: the domain used in the query
	:type source: string
	:param curious: ensure that the url is from the queried source
	:type curious: boolean

	'''
	url_obj = urlparse(url)
	if not url_obj: return None
	if not validate_url(url_obj, source, curious=curious): return None    
	try:
		time.sleep(15)
		headers = {'User-Agent': 'Mozilla/5.0'}
		article_req = requests.get(url, headers=headers)
		article_req.raise_for_status()
	except requests.exceptions.RequestException as e:
		logger.error('Web Scraper Error: {}'.format(str(e)))
		return None

	parser = 'html.parser'
	# if source == 'investopedia': parser = 'lxml'
	soup = BS(article_req.content, parser)

	paths = url_obj.path.split('/')[1:] # first entry is '' so exclude it
	p = paths[0].lower()
	if p in homepages(): return crawl_home_page(soup, p)
   
	pubdate = find_date(soup, source, paths[0])
	if pubdate is None and date_checker: return None
	article = find_article(soup, source, paths[0])
	logger.info('found pubdate to be: {}'.format(str(pubdate)))

	words = article.decode('utf-8').split(u' ')
	if length_checker and len(words) < 30: return None
	sentences = list(map(lambda s: s.encode('utf-8'), re.split(r' *[\.\?!][\'"\)\]]* *', article.decode('utf-8'))))
	industry, sector = '', ''
	
	# look for industry and sector values
	if ticker:
		google_url = 'https://www.google.com/finance?&q='+ticker
		try: 
			time.sleep(15)
			r = requests.get(google_url)
			r.raise_for_status()
		except requests.exceptions.RequestException as e:
			logger.warn('Web Scraper Error from google_url: {}'.format(str(e)))
			return WebNode(url, pubdate, article, words, sentences, industry, sector)
		
		s = BS(r.text, 'html.parser')
		# container = s.find('div', attrs= {'class':'sfe-section'}).findAll('a')
		container = s.find_all('a')
		next_ = False
		for a in container:
			if next_: 
				industry = a.text.strip()
				break
			if a.get('id') == 'sector': 
				sector = a.text.strip()
				next_ = True

	classification = -1000
	if ticker:	classification = classify(pubdate, ticker)
	
	return WebNode(url, pubdate, article, words, sentences, industry, sector, classification)

def classify(pubdate, ticker, offset=10):
	not_found = -1000
	
	today = datetime.today()
	today, pubdate = today.replace(tzinfo=None), pubdate.replace(tzinfo=None)
	margin = timedelta(days = 20) 
	if ((today - margin) > pubdate): return not_found

	url = 'https://www.google.com/finance/getprices?i=60&p=20d&f=d,o,h,l,c,v&df=cpct&q={}'.format(ticker.upper())
	try:
		time.sleep(15)
		req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
		req.raise_for_status()
	except: return not_found

	source_code = req.content
	split_source = source_code.split('\n')
	headers = split_source[:7] 
	stock_data = split_source[7:]

	if len(split_source) < 8: return not_found

	dates, highp, lowp = [], [], []
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

	bitmap = map(lambda timestamp: same_date(timestamp, pubdate), dates)
	if sum(bitmap) == 0: map(lambda timestamp: same_date(timestamp, pubdate+timedelta(hours=3)), dates) # possibly date was in PDT time
	if sum(bitmap) > 1: return not_found # this is an error case
	if sum(bitmap) == 0: 
		logger.warn('could not find associated stock price for ticker: %s' % ticker)
		return not_found
	
	idx = bitmap.index(1) # at this point, we know there is a match
	now = datetime.now()
	market_close = datetime(year=now.year, month=now.month, day=now.day, hour=16, minute=30)
	diff = (market_close.minute - dates[idx].minute)
	# print('date is ' + str(dates[idx]))
	# print ('price of pubdate is %d price of pubdate+offset is %d' % (highp[idx], highp[idx+offset]))
	# print('market_close is ' + str(market_close))
	# print('diff is %d' % diff)
	if pre_mrkt_close((dates[idx] + timedelta(minutes=offset)), market_close): return np.sign(highp[idx+offset] - highp[idx])
	elif diff > 0: 	return np.sign(highp[idx+diff] - highp[idx])
	else: return not_found
	
def same_date(date1, date2):
	if (date1.month == date2.month) and (date1.day == date2.day) and (date1.hour == date2.hour) and (date1.minute == date2.minute): return 1
	return 0

def pre_mrkt_close(date1, date2):
	if date1.hour < date2.hour: return True
	elif date1.minute < date2.minute: return True
	return False

def str2unix(datestr):
	date_UTC = datetime.fromtimestamp(int(datestr))	#	dates come in Unix time and converted to local 
	date1, date2 = datetime.now(timezone('US/Eastern')), datetime.now()
	rdelta = date1.hour - date2.hour 					#	convert local time to EST (the timezone the data was recorded in)
	return date_UTC + timedelta(hours=rdelta)	

# TESTS

# print(classify(datetime.now() - timedelta(days= 5, hours=9), 'tsla'))


# url = 'https://www.bloomberg.com/press-releases/2017-07-13/top-5-companies-in-the-global-consumer-electronics-and-telecom-products-market-by-bizvibe'
# url = 'https://www.bloomberg.com/gadfly/articles/2017-04-27/under-armour-earnings-buckle-up'
# url = 'https://www.bloomberg.com/news/videos/2017-04-27/under-armour-regains-footing-amid-footwear-slump-video'
# url = 'https://www.bloomberg.com/quote/UA:US'
# url = 'https://www.bloomberg.com/news/articles/2017-04-27/under-armour-loses-whatever-swagger-it-had-left'
# print (scrape(url, 'bloomberg', ticker='ua'))
#


# url = 'https://seekingalpha.com/article/4083816-kevin-plank-needs-resign-armour'
# url = 'https://seekingalpha.com/filing/3582573'
# url = 'https://seekingalpha.com/article/4077661-armour-millennial-play-pay'
# url = 'https://seekingalpha.com/news/3276278-retail-sector-awaits-nike-earnings'
# url = 'https://seekingalpha.com/article/4085681-armour-super-overvalued-shareholders-invested'
# url = 'https://seekingalpha.com/symbol/UA'
# print(scrape(url, 'seekingalpha'))



# url = 'http://www.reuters.com/article/under-armour-results-idUSL4N1HZ4CJ'
# url = 'http://www.reuters.com/article/us-britain-economy-investment-idUSKBN1A00TC'
# url = 'http://www.reuters.com/article/us-under-armour-results-idUSKBN17T1LI'
# url = 'http://www.reuters.com/finance/stocks/overview?symbol=UA.N'
# print(scrape(url, 'reuters'))



# url = 'http://www.investopedia.com/news/nike-declares-it-growth-company-nke/?lgl=rira-baseline-vertical'
# url = 'http://www.investopedia.com/markets/stocks/nke/'
# url = 
# url = 
# print(scrape(url, 'investopedia'))


# url = 'https://www.thestreet.com/story/14042017/1/stop-wondering-what-is-going-on-with-under-armour.html'
# url = 'https://www.thestreet.com/quote/UA.html'
# url = 
# url = 
# print(scrape(url, 'thestreet'))

