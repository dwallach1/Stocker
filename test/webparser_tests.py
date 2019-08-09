# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import sys
sys.path.append('/Users/david/Desktop/Stocker/src')
import math
import json
import csv
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
from stocker import earnings_watcher, Stocker

Test = namedtuple('Test', 'func status') # status {0,1} where 0 is failed, 1 is passed
Link = namedtuple('Link', 'url source')
verbose = False
EPSILON = 0.20

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
    return jaccard > (1 - EPSILON)

def valid_url_test():
    passed, failed = Test('valid_url_test', 1), Test('valid_url_test', 0)
    valid_urls = [      Link('https://www.bloomberg.com', 'bloomberg'), 
                        Link('https://www.google.com/finance', 'googlefinance'), 
                        Link('http://www.marketwatch.com', 'marketwatch'),
                        Link('http://www.investopedia.com/news/food-distributors-outperform-despite-amazon/', 'investopedia'),
                        Link('https://www.thestreet.com/story/14219936/1/gopro-shares-are-cheap-for-a-reason.html', 'thestreet'),
                        Link('https://www.msn.com/en-us/news/technology/paying-professors-inside-googles-academic-influence-campaign/ar-BBEfaQ3', 'msn')]
    
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

def cname_test():
    passed, failed = Test('cname_test', 1), Test('cname_test', 0)
    tickers = ['AAPL', 'GOOG', 'GPRO', 'TSLA', 'NFLX', 'AMZN', 'AMD']  
    sources = ['seekingalpha']  
    dm = Stocker(tickers, sources, csv_path=None, json_path=None)
    dm.build_queries(depth = 2)
    q2s = dm.queries[::2] #starting at index 2 (to get the cname query), get every second query
    for q in q2s:
        print(q)

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

def bloomberg_pr_error_test():
    passed, failed = Test('bloomberg_pr_error_test', 1), Test('bloomberg_pr_error_test', 0)
    url1 = 'https://www.bloomberg.com/press-releases/2017-11-01/gopro-announces-third-quarter-2017-results'
    url2 = 'https://www.bloomberg.com/press-releases/2017-11-06/proassurance-reports-results-for-third-quarter-2017'
    source = 'bloomberg'
    flags = {
                'date_checker': True, 
                'depth': 1, 
                'validate_url': False, 
                'length_check': True,
                'min_length': 100,            

    }
    web_node1 = scrape(url1, source, 'GPRO', flags)
    #web_node2 = scrape(url2, source, 'AAPL', flags)

    print (web_node1)
    d_webnode1 = dict(web_node1)
    print (d_webnode1.keys())
    
    print(d_webnode1['article'].split(' '))

    # with open('../data/test.csv', 'w') as f:
    #         fieldnames = d_webnode1.keys() # sort to ensure they are the same order every time
    #         writer = csv.DictWriter(f, fieldnames=fieldnames)
    #         writer.writeheader()
    #         writer.writerows(d_webnode1)





    #print (web_node2)

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
                # cname_test(),
                bloomberg_pr_error_test()
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

