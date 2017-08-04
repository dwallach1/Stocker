from __future__ import unicode_literals, print_function
import sys
sys.path.append('/Users/david/Desktop/Stocker/src')
from collections import namedtuple
from bs4 import BeautifulSoup 
import requests
from webparser import scrape

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

def homepage_test():
    failed, passed = Test('homepage_test', 0), Test('homepage_test', 1)
    homepages = [Link('https://www.bloomberg.com/quote/APRN:US', 'bloomberg'), # bloomberg
                 Link('https://seekingalpha.com/symbol/APRN', 'seekingalpha'),    # seekingalpha
                 Link('http://www.investopedia.com/markets/stocks/aprn/news/', 'investopedia'), # investopedia
                 Link('https://www.thestreet.com/quote/APRN.html', 'thestreet'), # thestreet
                 Link('https://www.reuters.com/finance/stocks/overview?symbol=APRN.N', 'reuters') #reuters
                 ]    
    urls = {
        'bloomberg': [  'https://www.bloomberg.com/news/articles/2017-08-02/the-magic-behind-many-unicorn-startups-complex-stock-contracts',
                        'http://www.investopedia.com/news/5-companies-amazon-killing/?utm_campaign=quote-bloomberg&utm_source=bloomberg&utm_medium=referral&utm_term=fb-capture&utm_content=/#ec|rss-bloomberg',
                        'https://www.bloomberg.com/news/articles/2017-07-25/blue-apron-shakes-up-executive-team-less-than-a-month-after-ipo',
                        'http://www.investopedia.com/news/blue-apron-jumps-analysts-call-troubled-ipo-buy/?utm_campaign=quote-bloomberg&utm_source=bloomberg&utm_medium=referral&utm_term=fb-capture&utm_content=/#ec|rss-bloomberg',
                        'https://www.thestreet.com/story/14239970/1/another-down-day-for-the-dow-as-ge-resumes-selloff-crude-trades-above-46.html?puc=bloomberg&cm_ven=BLOOMBERG',
                        'https://www.thestreet.com/story/14239970/1/another-down-day-for-the-dow-as-ge-resumes-selloff-crude-trades-above-46.html?puc=bloomberg&cm_ven=BLOOMBERG',
                        'https://www.bloomberg.com/news/articles/2017-07-24/blue-apron-soars-after-analysts-say-stock-is-a-bargain',
                        'https://www.thestreet.com/story/14239970/1/another-down-day-for-the-dow-as-ge-resumes-selloff-crude-trades-above-46.html?puc=bloomberg&cm_ven=BLOOMBERG',
                        'https://www.bloomberg.com/news/videos/2017-07-17/blue-apron-sinks-on-amazon-competition-video',
                        'https://www.bloomberg.com/news/articles/2017-07-17/blue-apron-plummets-after-amazon-files-for-meal-kit-trademark',
                        'https://www.bloomberg.com/news/articles/2017-07-11/snap-blue-apron-ipo-flops-show-fallout-of-lush-private-values',
                        'https://www.bloomberg.com/news/videos/2017-06-30/blue-apron-falls-below-ipo-price-may-need-cash-video',
                        'https://www.bloomberg.com/news/videos/2017-06-29/why-blue-apron-s-stock-fizzled-in-debut-video',
                        'https://www.bloomberg.com/news/articles/2017-06-28/blue-apron-said-to-raise-300-million-after-slashing-ipo-price',
                        'https://www.bloomberg.com/news/articles/2017-06-29/blue-apron-may-need-to-raise-more-money-soon-after-shrunken-ipo',
                        'https://www.bloomberg.com/news/audio/2017-06-28/bloomberg-markets-blue-apron-slashes-ipo-price-34',
                        'https://www.bloomberg.com/news/videos/2017-06-28/how-amazon-whole-foods-deal-could-impact-blue-apron-video',
                        'https://www.bloomberg.com/news/articles/2017-06-28/blue-apron-aspires-to-amazon-com-like-valuation-in-u-s-ipo',
                        'https://www.bloomberg.com/news/articles/2017-06-28/blue-apron-meal-kit-company-slashes-ipo-price-to-11-a-share',
                        'https://www.bloomberg.com/news/videos/2017-06-20/food-delivery-heats-up-with-blue-apron-ipo-video',
                        'https://www.bloomberg.com/press-releases/2017-07-26/glancy-prongay-murray-llp-commences-investigation-on-behalf-of-blue-apron-holdings-inc-investors',
                        'https://www.bloomberg.com/press-releases/2017-07-26/scott-scott-attorneys-at-law-llp-announces-investigation-into-blue-apron-holdings-inc-aprn',
                        'https://www.bloomberg.com/press-releases/2017-07-26/act-now-monteverde-associates-pc-announces-an-investigation-of-blue-apron-holdings-inc-aprn',
                        'https://www.bloomberg.com/press-releases/2017-07-25/blue-apron-holdings-inc-announces-changes-to-executive-leadership-team',
                        'https://www.bloomberg.com/press-releases/2017-07-24/blue-apron-holdings-investor-alert-faruqi-faruqi-llp-encourages-investors-who-suffered-losses-exceeding-100-000-investing',
                        'https://www.bloomberg.com/press-releases/2017-07-24/lifshitz-miller-llp-announces-investigation-of-blue-apron-holdings-inc-irobot-corporation-monogram-residential-trust-inc',
                        'https://www.bloomberg.com/press-releases/2017-07-19/shareholder-alert-bronstein-gewirtz-grossman-llc-announces-investigation-of-blue-apron-holdings-inc-aprn',
                        'https://www.bloomberg.com/press-releases/2017-07-19/shareholder-alert-levi-korsinsky-llp-notifies-investors-of-an-investigation-involving-possible-securities-fraud-violations-j5b51ttv',
                        'https://www.bloomberg.com/press-releases/2017-07-18/blue-apron-holdings-investor-alert-faruqi-faruqi-llp-encourages-investors-who-suffered-losses-exceeding-100-000-investing',
                        'https://www.bloomberg.com/press-releases/2017-07-18/harwood-feffer-llp-announces-investigation-of-blue-apron-holdings-inc'
                        ]

    }

    for link in homepages: 
        sysprint ('Homepage test -- testing {}'.format(link.source))
        result = scrape(link.url, link.source)
        if not (isinstance(result, list)): return failed
        if (len(result) != len(urls[link.source])): return failed
        for l in urls[link.source]:
            if not (l in result): return failed
        sysprint( bcolors.GREEN + 'Home Page Test: Passed' + bcolors.ENDC)
        return passed

    return passed

def bloomberg_test():
    pass
    # sysprint ('testing bloomberg')
    # article = 'ariasflfkdksmfsd'
    # result = get_article()
    # Assert (get_article(bloomberg_url) == article)
    # Date = datetime(date)
    # Assert (get_date(bloomberg_url == date)
    # sysprint(bcolors.GREEN + 'Passed Bloomberg Page Test')
    
#[REPEAT FOR ALL TESTED DOMAINS]


def decompose_article_test():
    failed, passed = Test('decompose_article_test', 0), Test('decompose_article_test', 1)
    # article = 'this is an article. This is a sentence! Can you parse it?\n Can you..?'
    # words = ['this', 'is', 'an', 'article', 'This', 'is', 'a', 'sentence', 
    #         'Can', 'you', 'parse', 'it', 'Can', 'you', 'parse', 'it', 'Can', 'you']
    # sents = ['this is an article.', 'This is a sentence!', 'Can you parse it?', 'Can you..?']
    url = 'https://www.bloomberg.com/news/articles/2017-07-25/blue-apron-shakes-up-executive-team-less-than-a-month-after-ipo'
    link = Link(url, 'bloomberg')
    wn = scrape(link.url, link.source, words=True, sentences=True)
    print (wn.sentences)
    return passed

def main():
    tests = [decompose_article_test()]
    passed = sum(map(lambda test: test.status, tests))
    total = len(tests)
    sysprint ('passed {} out of {} test cases'.format(passed, total))

if __name__ == "__main__":
    main()
    

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
