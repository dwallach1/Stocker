# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import sys
sys.path.append('/Users/david/Desktop/Stocker/src')
import math
import json
import argparse
import re
from collections import namedtuple
from datetime import datetime
from urlparse import urlparse
from bs4 import BeautifulSoup 
import requests
from nltk import word_tokenize
from pytz import timezone
from numpy.testing import assert_almost_equal
from webparser import scrape, validate_url, str2date, get_sector_industry, classify
from stocker import earnings_watcher

Test = namedtuple('Test', 'func status') # status {0,1} where 0 is failed, 1 is passed
Link = namedtuple('Link', 'url source')
verbose = False
EPSILON = 0.80

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

def similar_dates(date1, date2): return date1.year == date2.year and date1.month == date2.month and date1.day == date2.day and date1.hour == date2.hour and date1.minute == date2.minute 

def clean(text): 
    replacements = {
        '\u2019', '\'',
        '\u2014', ' ',
        '\u201d', ' ',
        '\u201c', '“',
        '\u201d', '”'
    }
    return text.decode('utf-8').replace(u'\u2019', '\'').replace('\r', ' ').replace('\n', ' ').split(' ')

def jaccard_coeff(test_article, bucket):
    """
    returns a number between 0 and 1 defining the amount of words in both over the total amount of words
    test_article, control_article = A, B
    -- split aricles by words to compare -- doesn't consider term freq & rare terms carry more weight
    jaccard(A, B) = | A intersect B | / | A union B |
    jaccard(A, A) = 1
    jaccard(A, B) = 0 if A intersect B = 0
    Sets do not have to be the same size
    """
    with open('articles.json', 'r') as f:
        data = json.load(f, encoding='utf-8', strict=False)
    control_article = re.sub('\s+', ' ', data[bucket]).encode('utf-8').decode('utf-8').replace(u'\u2019', '\'').split(' ')
    test_article = test_article.decode('utf-8').replace('\n', ' ').split(' ')

    A, B = set(test_article), set(control_article)
    jaccard = float(len(A.intersection(B)) / len(A.union(B)))
    print ('jaccard coefficient is: {} for {}'.format(jaccard, bucket))
    return jaccard > EPSILON

def valid_url_test():
    passed, failed = Test('valid_url_test', 1), Test('valid_url_test', 0)
    valid_urls = [      Link('https://www.bloomberg.com', 'bloomberg'), 
                        Link('https://www.google.com/finance', 'googlefinance'), 
                        Link('http://www.marketwatch.com', 'marketwatch'),
                        Link('http://www.investopedia.com/news/food-distributors-outperform-despite-amazon/', 'investopedia'),
                        Link('https://www.thestreet.com/story/14219936/1/gopro-shares-are-cheap-for-a-reason.html', 'thestreet')]
    
    invalid_urls = [    Link('asd://www.bloomberg.com', 'bloomberg'), 
                        Link('www.investing.com', 'investing'), 
                        Link('htps://seekingalpha.com', 'seekingalpha')]
    for link in valid_urls:
        if not validate_url(urlparse(link.url), link.source):
            if verbose: print('valid_url_test: error for link: {}'.format(link.url))
            return failed
    for link in invalid_urls:
        if validate_url(urlparse(link.url), link.source):
            if verbose: print('valid_url_test: error for link: {}'.format(link.url))
            return failed

    curious = [     Link('https://www.bloomberg.com', 'seekingalpha'), 
                    Link('https://www.google.com/finance', 'blah_blah'), 
                    Link('http://www.marketwatch.com', 'questions')]
    for link in curious:
        if not validate_url(urlparse(link.url), link.source, curious=True): 
            if verbose: print('valid_url_test: error for link: {}'.format(link.url))
            return failed

    return passed

def str2date_test():
    passed, failed = Test('str2date_test', 1), Test('str2date_test', 0)
    Date = namedtuple('Date', 'string dtime')
    # datetime(year, month, day[, hour[, minute[, second[, microsecond[,tzinfo]]]]])
    dates = [   Date('1502062730', datetime(2017, 8, 6, 19, 38)),
                Date('150206290', datetime(1974, 10, 5, 7, 58)),
                Date('1502000000', datetime(2017, 8, 6, 2, 13)),
                Date('1501000000', datetime(2017, 7, 25, 12, 26)),
                Date('1510321300', datetime(2017, 11, 10, 8, 41)),
                Date('1501853400', datetime(2017, 8, 4, 9, 30))]
    for date in dates:
        d = str2date(date.string)
        dt = date.dtime
        if (dt.year != d.year) or (dt.hour != d.hour) or (dt.minute != d.minute):
            if verbose: print('str2date_test: error for date {}'.format(date.string))
            return failed
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
        if industry != stock.industry or sector != stock.sector: 
            if verbose: print('get_sector_industry_test: error for stock: {}'.format(stock.ticker))
            return failed  
    return passed

def classify_test():    # also a dynamic test in some cases -- until we link to paid database
    passed, failed = Test('classify_test', 1), Test('classify_test', 0)
    Classifier = namedtuple('Classifier', 'ticker date status magnitude offset')
    classifications = [ Classifier('aapl',  datetime(2017, 8, 4, 9, 32), 1.0, 0.905, 10),       # 155.845 | 156.75
                        Classifier('amzn',  datetime(2017, 7, 31, 14, 20), -1.0, 0.52, 10),     # 992.26 | 991.74
                        Classifier('bac',   datetime(2017, 8, 2, 10, 36), -1.0, 0.026, 10),     # 24.34 | 24.28  -- 24.314
                        Classifier('ge',    datetime(2017, 8, 2, 13, 22), -1.0, 0.009, 120),    # 25.515 | 25.506
                        Classifier('tsla',  datetime(2017, 7, 31, 12, 12), -1.0, -2.457, 124),  # 326.147 | 323.69
                        Classifier('tsla',  datetime(2017, 8, 6, 13, 22), -100, 0, 124),        # date on weekend   
                        Classifier('nke',   datetime(2016, 8, 4, 15, 54), -1000, 0, 5)]         # time + offset > market close
    for c in classifications:
        result = classify(c.date, c.ticker, offset=c.offset) 
        if (result.status != c.status):
            try: assert_almost_equal(result.magnitude,c.magnitude)
            except:
                if verbose: print ('classify_test: Wrong classification for stock: {} on date {} with offset {}'.format(c.ticker, c.date, c.offset))
                return failed
    return passed

"""
DYNAMIC URL TESTS

these tests have to be constantly updated because the content on the webpages is always changing hence the 'dynamic'
nature. These tests are more so to ensure that the content being generated from the webparser is the correct format
and looks generally as expected.

I use the cosine similarity to check if the webparser gets the correct article from the url because the parsing
process is susceptible to noise such as headers, advertiesements, etc. By changing the EPSILON variable, you can
determine how strict the tests are
"""

def yahoo_test():
    passed, failed = Test('yahoo_test', 1), Test('yahoo_test', 0)
    source = 'yahoofinance'
    
    # normal url result test
    url = 'https://finance.yahoo.com/news/blue-apron-aprn-investors-apos-174305777.html'
    result = scrape(url, source)
    if not isinstance(result.article, str): return failed
    if not similar_dates(result.pubdate, datetime(2017, 7, 11, 13, 43, tzinfo=timezone('US/Eastern'))): return failed
    if not jaccard_coeff(result.article, 'yahoofinance+news'): return failed
    
    homeurl = 'https://finance.yahoo.com/quote/APRN?p=APRN'
    home_result = scrape(homeurl, source)
    if not isinstance(home_result, list): return failed
    if len(home_result) < 1: return failed
    # for link in home_result: print(link)
    return passed

def bloomberg_test():
    passed, failed = Test('bloomberg_test', 1), Test('bloomberg_test', 0)
    source = 'bloomberg'
    
    # normal url result test
    url = 'https://www.bloomberg.com/news/articles/2017-08-04/blue-apron-plans-to-cut-24-of-staff-barely-a-month-since-ipo'
    result = scrape(url, source)
    if not isinstance(result.article, str): return failed
    if not similar_dates(result.pubdate, datetime(2017, 8, 4, 11, 58, tzinfo=timezone('US/Eastern'))): return failed
    if not jaccard_coeff(result.article, 'bloomberg+news'): return failed
    
    # press release result test
    url_pr = 'https://www.bloomberg.com/press-releases/2017-08-01/marathon-kids-run-all-50-states'
    pr_result = scrape(url_pr, source)
    if not isinstance(pr_result.article, str): return failed
    if not similar_dates(pr_result.pubdate, datetime(2017, 8, 1, 13, 0, tzinfo=timezone('US/Eastern'))): return failed
    if not jaccard_coeff(pr_result.article, 'bloomberg+press-releases'): return failed
    
    # homepage result test
    homeurl = 'https://www.bloomberg.com/quote/APRN:US'
    home_result = scrape(homeurl, source)
    if not isinstance(home_result, list): return failed
    if len(home_result) < 1: return failed
    # for link in home_result: print(link)
    return passed

def seekingalpha_test():
    passed, failed = Test('seekingalpha_test', 1), Test('seekingalpha_test', 0)
    homeurl = 'https://seekingalpha.com/symbol/GE'
    url = 'https://seekingalpha.com/article/4093388-general-electric-breaking-drink-kool-aid'
    source = 'seekingalpha'
    result = scrape(url, source)
    if not isinstance(result.article, str): return failed
    if not similar_dates(result.pubdate, datetime(2017, 8, 2, 8, 1, 0, tzinfo=timezone('US/Eastern'))): return failed
    home_result = scrape(homeurl, source)
    if not isinstance(home_result, list): return failed
    if len(home_result) < 1: return failed
    # for link in home_result: print(link)
    return passed

def reuters_test():
    passed, failed = Test('reuters_test', 1), Test('reuters_test', 0)
    homeurl = 'https://www.reuters.com/finance/stocks/overview?symbol=NKE.N'
    url = 'https://www.reuters.com/article/us-under-armour-strategy-analysis-idUSKBN1AK2H6'
    source = 'reuters'
    result = scrape(url, source)
    if not isinstance(result.article, str): return failed
    if not similar_dates(result.pubdate, datetime(2017, 8, 4, 18, 4, 0, tzinfo=timezone('US/Eastern'))): return failed
    home_result = scrape(homeurl, source)
    if not isinstance(home_result, list): return failed
    if len(home_result) < 1: return failed
    # for link in home_result: print(link)
    return passed

def investopedia_test():
    passed, failed = Test('investopedia_test', 1), Test('investopedia_test', 0)
    homeurl = 'http://www.investopedia.com/markets/stocks/amzn/'
    url = 'http://www.investopedia.com/news/food-distributors-outperform-despite-amazon/'
    source = 'investopedia'
    result = scrape(url, source)
    if not isinstance(result.article, str): return failed
    if not similar_dates(result.pubdate, datetime(2017, 8, 9, 17, 9, 0, tzinfo=timezone('US/Eastern'))): return failed
    home_result = scrape(homeurl, source)
    if not isinstance(home_result, list): return failed
    if len(home_result) < 1: return failed
    # for link in home_result: print(link)
    return passed

def thestreet_test():
    passed, failed = Test('thestreet_test', 1), Test('thestreet_test', 0)
    homeurl = 'https://www.thestreet.com/quote/GPRO.html'
    url = 'https://www.thestreet.com/story/14219936/1/gopro-shares-are-cheap-for-a-reason.html'
    source = 'thestreet'
    result = scrape(url, source)
    if not isinstance(result.article, str): return failed
    print('street pubdate: ' + str(result.pubdate))
    print (result.article)
    if not similar_dates(result.pubdate, datetime(2017, 8, 3, 16, 15, 0, tzinfo=timezone('US/Eastern'))): return failed
    print ('passed thestreet datetest')
    home_result = scrape(homeurl, source)
    if not isinstance(home_result, list): return failed
    if len(home_result) < 1: return failed
    # for link in home_result: print(link)
    return passed

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
    
def main():
    parser = argparse.ArgumentParser(description='Test cases for Stocker program')
    parser.add_argument('-v','--verbose', help='verbose printing for error cases', action='store_true', required=False)
    args = vars(parser.parse_args())
    if args['verbose']:
        global verbose
        verbose = True
    tests = [   
                # valid_url_test(), 
                # str2date_test(), 
                # get_sector_industry_test(), 
                # classify_test(),
                yahoo_test(),
                bloomberg_test()
                # seekingalpha_test(),
                # reuters_test(),
                # investopedia_test()
                # thestreet_test()
            ]
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

