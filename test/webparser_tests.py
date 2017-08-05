from __future__ import unicode_literals, print_function
import sys
sys.path.append('/Users/david/Desktop/Stocker/src')
from collections import namedtuple
from bs4 import BeautifulSoup 
import requests
from webparser import scrape
from stocker import earnings_watcher

Test = namedtuple('Test', 'func status') # status {0,1} where 0 is failed, 1 is passed
Link = namedtuple('Link', 'url source')

class bcolors: 
    GREEN = '\033[92m'
    FAIL = '\033[91m' 
    ENDC = '\033[0m'

def sysprint(text):
    sys.stdout.write('\r{}\033[K'.format(text))
    sys.stdout.flush()

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
    # valid_urls = []
    # invalid_urls = []
    # for url in valid_urls:    
    pass

def classify_test():
    pass
    # datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    # stock, date, offset = 'APRN', datetime(2017, 07, 12, 9, 33), 10  # HAVE CLASSIFY RETURN A MAGNITUDE ALSO (the size of difference)
    # 7.105 --> 7.11
    # change = classify(stock, date, offset)
    # assert(classify(change.sign == 1.00 && change.magnitude(.005))
    # stock, date, offset = 'NKE', datetime(), 13
    # assert(classify(stock, date, offset) == 0.00)
    # stock, date, offset = 'TSLA', datetime(), 20
    # assert(classify(stock, date, offset) == -1.00)

    # # Test market close 
    # stock, date, offset = 'APRN', datetime(), 10
    # assert(classify(stock, date, offset) == 1.00)

    # # test if pubdate was after market close / before
    # stock, date, offset = 'APRN', datetime(), 10
    # assert(classify(stock, date, offset) == 1.00)

    # # test article published on weekend
    # stock, date, offset = 'APRN', datetime(), 10
    # assert(classify(stock, date, offset) == 1.00)

def str2unix_test():
    pass

def earnings_watcher_test():
    passed, failed = Test('earnings_watcher_test', 1), Test('earnings_watcher_test', 0)
    stocks = earnings_watcher()
    print (stocks)
    return passed


def main():
    # tests = [str2unix_test(), classify_test(), valid_url_test()]
    tests = [earnings_watcher_test()]
    passed = 0
    for test in tests:
        passed += test.status
        color = bcolors.GREEN if test.status == 1 else bcolors.FAIL
        status = ' passed' if test.status == 1 else ' failed'
        print (color + test.func + status + bcolors.ENDC)
    # passed = sum(map(lambda test: test.status, tests))
    # total = len(tests)
    print ('\n------------------------------')
    print ('passed {} out of {} test cases'.format(passed, len(tests)))

if __name__ == "__main__":
    main()
 

# ------------------------ 
#
#  DYNAMIC URL TESTS
#
# ------------------------    

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
