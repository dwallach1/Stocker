
"""
notes:

- quant has nothing to do with the company, it uses patterns and numbers to determine
- fundamental data is data concerning the company

# Alpha		: how much of your gains were made irrespective to the market
# Beta		: how much of your gains were made respective to the market ({-0.3, +0.3}, aim for 0)
# Sharpe	: how much risk you took on compared to how much you made (must be > 1 -- 3 is great)
 

# moving average : good at detecting trends
# Max-dropdown : highest high to the lowest subsequent fall (cycle based not full history)

- price to book ratio (pb): how much are all tangible assets vs price of the stock
- price to equity ratio (pe): 
"""
import re, logging
from urlparse import urlparse
import requests
from datetime import datetime 
import dateutil.parser as dateparser
import pysentiment as ps 
from bs4 import BeautifulSoup as BS

logger = logging.getLogger(__name__)

class WebNode(object):
    """represents an entry in data.csv that will be used to train our neural network"""
    def __init__(self, url, pubdate, article, words, sentences, industry, sector):
        self.url = url              # string
        self.pubdate = pubdate      # datetime
        self.article = article      # article
        self.words = words          # list
        self.sentences = sentences  # list
        self.industry = industry    # string
        self.sector = sector        # string
        self.score = ps.LM().get_score(words)
        self.subjectivity = self.score['Subjectivity']
        self.polarity = self.score['Polarity']
        self.negative = self.score['Negative']
        self.positive = self.score['Positive']


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
    ID = ID.lower()
    if ID == 'quote':       # bloomberg
        urls = soup.find_all('a', attrs={'class': 'news-story__url'}, href=True)
        if not (urls is None): return list(map(lambda url: url['href'], urls)); return None        
    elif ID == 'symbol':  # seeking alpha
        base = 'https://seekingalpha.com'
        urls = soup.find_all('a', attrs={'sasource': 'qp_latest'}, href=True)
        if not (urls is None): return list(map(lambda url: base + url['href'], urls)); return None  
    elif ID == 'finance':   # reuters
        base = 'http://reuters.com'
        urls = soup.find('div', attrs={'id': 'companyOverviewNews'})
        if not (urls is None): return list(map(lambda url: base + url['href'], urls.find_all('a'))); return None
    return None


def scrape(url, source, curious=False, ticker=None, date_checker=True, length_checker=False, min_length=30, crawl_page=False):
    url_obj = urlparse(url)
    if not url_obj: return None
    if not validate_url(url_obj, source, curious=curious): return None    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        article_req = requests.get(url, headers=headers)
        article_req.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error('Web Scraper Error: {}'.format(str(e)))
        return None

    paths = url_obj.path.split('/')[1:] # first entry is '' so exclude it

    soup = BS(article_req.content, 'html.parser')
    p = paths[0].lower()
    if p in ['quote', 'symbol', 'finance']: return crawl_home_page(soup, p)
   
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
            r = requests.get(google_url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print('Web Scraper Error from google_url: {}'.format(str(e)))
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

    return WebNode(url, pubdate, article, words, sentences, industry, sector)



# TESTS
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



# url = 
# url = 
# url = 
# url = 
# print(scrape(url, 'investopedia'))


# url = 
# url = 
# url = 
# url = 
# print(scrape(url, 'thestreet'))







