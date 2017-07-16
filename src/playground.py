#from zipline.api import order_target, record, symbol


# zipline : https://github.com/quantopian/zipline
# still need to : pip install zipline [done]


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
import requests
from urlparse import urlparse
from datetime import datetime 
import dateutil.parser as dateparser
from bs4 import BeautifulSoup as BS


def validate_url(url_obj, source, curious=False):
    valid_schemes = ['http', 'https']
    domain = list(filter(lambda x: len(x) > 3, url_obj.hostname.split('.')))[0].lower()
    return (url_obj.scheme in valid_schemes) and ((domain == source.lower()) or curious)

def find_date(soup, source, container):
    s, c = source.lower(), container.lower()
    if s == 'BLOOMBERG':
        if c == 'PRESS-RELEASES': 
            return dateparser.parse(soup.find('span', attrs={'class': 'date'}).text.strip(), fuzzy=True)
        return dateparser.parse(soup.find('time').text.strip(), fuzzy=True)
    elif s == 'SEEKINGALPHA':
        if c == 'FILING': return None
        return dateparser.parse(soup.find('time', attrs={'itemprop': 'datePublished'})['content'], fuzzy=True)
    elif s == 'REUTERS':
        return dateparser.parse(''.join(soup.find('div', attrs={'class': 'ArticleHeader_date_V9eGk'}).text.strip().split('/')[:2]), fuzzy=True)
    return None


def crawl_home_page(soup, p):
    

def scrape(url, source, curious=False):
    url_obj = urlparse(url)
    if not validate_url(url_obj, source, curious=curious): return None
    print('URL has been validated and accepted')
    
    try: 
        req = requests.get(url)
        req.raise_for_status()
    except requests.exceptions.Timeout:
        print('Web Scraper Error opening {} due to Timeout'.format(url))
    except requests.exceptions.TooManyRedirects:
        print('Web Scraper Error opening {} due to Too many Redirects'.format(url))
    except requests.exceptions.RequestException as e:
        print('Web Scraper Error opening {} due to Timeout'.format(str(e)))

    paths = url_obj.path.split('/')[1:] # first entry is '' so exclude it

    soup = BS(req.content, "html.parser")
    p = paths[0].lower()
    if p in ['quote', 'symbol', 'finance']: return crawl_home_page(soup, p)
   
    date = find_date(soup, source, paths[0])
    print('found date to be: {}'.format(str(date)))


# url = 'https://www.bloomberg.com/press-releases/2017-07-13/top-5-companies-in-the-global-consumer-electronics-and-telecom-products-market-by-bizvibe'
# # url = 'https://www.bloomberg.com/gadfly/articles/2017-04-27/under-armour-earnings-buckle-up'
# # url = 'https://www.bloomberg.com/quote/UA:US'
# # url = 'https://www.bloomberg.com/news/articles/2017-04-27/under-armour-loses-whatever-swagger-it-had-left'
# scrape(url, 'bloomberg')
#


# url = 'https://seekingalpha.com/article/4083816-kevin-plank-needs-resign-armour'
# url = 'https://seekingalpha.com/filing/3582573'
# url = 'https://seekingalpha.com/article/4077661-armour-millennial-play-pay'
# url = 'https://seekingalpha.com/news/3276278-retail-sector-awaits-nike-earnings'
# url = 'https://seekingalpha.com/article/4085681-armour-super-overvalued-shareholders-invested'
# url = 'https://seekingalpha.com/symbol/UA'
# scrape(url, 'seekingalpha')



url = 'http://www.reuters.com/article/under-armour-results-idUSL4N1HZ4CJ'
# url = 'http://www.reuters.com/article/us-britain-economy-investment-idUSKBN1A00TC'
# url = 'http://www.reuters.com/article/us-under-armour-results-idUSKBN17T1LI'
# url = 'http://www.reuters.com/finance/stocks/overview?symbol=UA.N'
scrape(url, 'reuters')


# from zipline.api import order_target, record, symbol


# def initialize(context):
#     context.i = 0
#     context.asset = symbol('AAPL')


# def handle_data(context, data):
#     # Skip first 300 days to get full windows
#     context.i += 1
#     if context.i < 300:
#         return

#     # Compute averages
#     # data.history() has to be called with the same params
#     # from above and returns a pandas dataframe.
#     short_mavg = data.history(context.asset, 'price', bar_count=100, frequency="1d").mean()
#     long_mavg = data.history(context.asset, 'price', bar_count=300, frequency="1d").mean()

#     avg_minute_price = data.history(context.asset, 'price', frequency="1m").mean()

#     log.info(short_mavg)
#     log.info(long_mavg)
#     # Trading logic
#     if short_mavg > long_mavg:
#         # order_target orders as many shares as needed to
#         # achieve the desired number of shares.
#         order_target(context.asset, 100)
#     elif short_mavg < long_mavg:
#         order_target(context.asset, 0)

#     # Save values for later inspection
#     record(AAPL=data.current(context.asset, 'price'),
#            short_mavg=short_mavg,
#            long_mavg=long_mavg)
#     # read_pd()




