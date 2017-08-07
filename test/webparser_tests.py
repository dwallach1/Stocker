from __future__ import unicode_literals, print_function
import sys
sys.path.append('/Users/david/Desktop/Stocker/src')
from collections import namedtuple
from datetime import datetime
from urlparse import urlparse
from bs4 import BeautifulSoup 
import requests
from webparser import scrape, validate_url, str2unix, get_sector_industry, classify
from stocker import earnings_watcher

Test = namedtuple('Test', 'func status') # status {0,1} where 0 is failed, 1 is passed
Link = namedtuple('Link', 'url source')
verbose = True

class bcolors: 
    GREEN = '\033[92m'
    FAIL = '\033[91m' 
    ENDC = '\033[0m'
    BOLD = "\033[;1m"

def soupify(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = requests.get(url, headers=headers)
        if req.status_code == 503:
            logger.warn('Request code of 503')
            time.sleep(GOOGLE_WAIT)
            req = requests.get(url, headers=headers) 
    except requests.exceptions.RequestException as e:
        print(bcolors.FAIL + 'Web Scraper Error: {}'.format(str(e)) + bcolors.ENDC)
        return None

    return BeautifulSoup(req.content, 'html.parser')

def valid_url_test():
    passed, failed = Test('valid_url_test', 1), Test('valid_url_test', 0)
    valid_urls = [      Link('https://www.bloomberg.com', 'bloomberg'), 
                        Link('https://www.google.com/finance', 'google'), 
                        Link('http://www.marketwatch.com', 'marketwatch')]
    invalid_urls = [    Link('asd://www.bloomberg.com', 'bloomberg'), 
                        Link('www.investing.com', 'investing'), 
                        Link('htps://seekingalpha.com', 'seekingalpha')]
    for link in valid_urls:
        if not validate_url(urlparse(link.url), link.source): return failed
    for link in invalid_urls:
        if validate_url(urlparse(link.url), link.source): return failed

    curious = [     Link('https://www.bloomberg.com', 'seekingalpha'), 
                    Link('https://www.google.com/finance', 'blah_blah'), 
                    Link('http://www.marketwatch.com', 'questions')]
    for link in curious:
        if not validate_url(urlparse(link.url), link.source, curious=True): return failed

    return passed

def str2unix_test():
    passed, failed = Test('str2unix_test', 1), Test('str2unix_test', 0)
    Date = namedtuple('Date', 'string dtime')
    # datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    dates = [   Date('1502062730', datetime(2017, 8, 6, 19, 38)),
                Date('150206290', datetime(1974, 10, 5, 7, 58)),
                Date('1502000000', datetime(2017, 8, 6, 2, 13)),
                Date('1501000000', datetime(2017, 7, 25, 12, 26)),
                Date('1510321300', datetime(2017, 11, 10, 8, 41))]
    for date in dates:
        d = str2unix(date.string)
        dt = date.dtime
        if (dt.year != d.year) or (dt.hour != d.hour) or (dt.minute != d.minute): return failed
    return passed

def get_sector_industry_test():
    passed, failed = Test('get_sector_industry_test', 1), Test('get_sector_industry_test', 0)
    Stock = namedtuple('Stock', 'ticker industry sector')
    stocks = [  Stock('UA', 'Apparel & Accessories - NEC', 'Cyclical Consumer Goods & Services'),
                Stock('AMZN', 'Internet & Mail Order Department Stores', 'Cyclical Consumer Goods & Services'),
                Stock('APRN', 'Food Processing - NEC', 'Non-Cyclical Consumer Goods & Services'),
                Stock('GE', 'Industrial Conglomerates', 'Industrials'),
                Stock('BAC', 'Banks - NEC', 'Financials')]
    for stock in stocks:
        industry, sector = get_sector_industry(stock.ticker)
        if industry != stock.industry or sector != stock.sector: return failed  
    return passed

def classify_test():
    passed, failed = Test('classify_test', 1), Test('classify_test', 0)
    # datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    Classifier = namedtuple('Classifier', 'ticker date status magnitude')
    classifications = [ Classifier('amzn', datetime(2017, 8, 1, 12, 30), -1.0, 0.86),    # 999.87 | 999.01
                        Classifier('AAPL', datetime(2017, 7, 31, 14, 18), 1.0, 0.651),   # 148.64 | 148.715
                        Classifier('bac', datetime(2017, 8, 2, 10, 36), 1.0, 0.10),      # 24.34 | 24.44
                        Classifier('ge', datetime(2017, 8, 1, 20, 30), -1000, 0),        # POST MARKET CLOSE
                        Classifier('nke', datetime(2016, 8, 4, 15, 54), -1000, 0)]       # time + offset > market closes 
    for c in classifications:
        result = classify(c.date, c.ticker) 
        print ('result is: {} | {} -- it should be {} | {}'.format(result.status, result.magnitude, c.status, c.magnitude))
        if (result.status != c.status): 
            if verbose: print ('classify_test: Wrong classification for stock: {} on date {} with offset {}'.format(c.ticker, c.date, 10))
            return failed

    # classifications = [ Classifier('amzn', datetime(2017, 8, 1, 12, 30), -1.0, 0.86),    # 999.87 | 999.01
    #                     Classifier('AAPL', datetime(2017, 7, 31, 14, 18), 1.0, 0.651),   # 148.64 | 148.715
    #                     Classifier('bac', datetime(2017, 8, 2, 10, 36), 1.0, 0.10),      # 24.34 | 24.44
    #                     Classifier('ge', datetime(2017, 8, 1, 20, 30), -1000, 0),        # POST MARKET CLOSE
    #                     Classifier('nke', datetime(2016, 8, 4, 15, 54), -1000, 0)]       # time + offset > market closes 
   
    # for c in classifications:
    #     result = classify(c.date, c.ticker, offset=25) 
    #     if (result.status != c.status) or (result.magnitude != c.magnitude): return failed

    return passed
    

def main():
    tests = [valid_url_test(), str2unix_test(), get_sector_industry_test(), classify_test()]
    passed = 0
    for test in tests:
        passed += test.status
        color = bcolors.GREEN if test.status == 1 else bcolors.FAIL
        status = ' passed' if test.status == 1 else ' failed'
        print (bcolors.BOLD + test.func + ':' + color + status + bcolors.ENDC)
    print ('------------------------------')
    print ('passed {} out of {} test cases'.format(passed, len(tests)))

if __name__ == "__main__":
    main()
 

"""
DYNAMIC URL TESTS

these tests have to be constantly updated because the content on the webpages is always changing hence the 'dynamic'
nature. These tests are more so to ensure that the content being generated from the webparser is the correct format
and looks generally as expected.
"""

def yahoo_test():
    url = 'https://finance.yahoo.com/quote/APRN?p=APRN'
    pass

def earnings_watcher_test():
    passed, failed = Test('earnings_watcher_test', 1), Test('earnings_watcher_test', 0)
    stocks = earnings_watcher()
    if not (isinstance(stocks, list)): return failed
    return passed

def dryscrape_test():
    passed, failed = Test('dryscrape_test', 1), Test('dryscrape_test', 0)
    # url = 'http://www.investopedia.com/markets/stocks/aprn/'
    url = 'https://www.thestreet.com/quote/APRN.html'
    urls = scrape(url, 'thestreet')
    print (urls)
    return passed

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
