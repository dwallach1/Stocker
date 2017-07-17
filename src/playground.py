
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
import re
import requests
from urlparse import urlparse
from datetime import datetime 
import dateutil.parser as dateparser
from bs4 import BeautifulSoup as BS


class WebNode(object):
    """represents an entry in data.csv that will be used to train our neural network"""
    def __init__(self, pubdate, article, words, sentences, industry='', sector=''):
        self.pubdate = pubdate      # datetime
        self.article = article      # article
        self.words = words          # list
        self.sentences = sentences  # list
        self.industry = industry    # string
        self.sector = sector        # string


def validate_url(url_obj, source, curious=False):
    valid_schemes = ['http', 'https']
    domain = list(filter(lambda x: len(x) > 3, url_obj.hostname.split('.')))[0].lower()
    return (url_obj.scheme in valid_schemes) and ((domain == source.lower()) or curious)

def find_date(soup, source, container):
    s, c = source.lower(), container.lower()
    if s == 'bloomberg':
        if c == 'press-releases': 
            return dateparser.parse(soup.find('span', attrs={'class': 'pubdate'}).text.strip(), fuzzy=True)
        return dateparser.parse(soup.find('time').text.strip(), fuzzy=True)
    elif s == 'seekingalpha':
        if c == 'filing': return None
        return dateparser.parse(soup.find('time', attrs={'itemprop': 'datePublished'})['content'], fuzzy=True)
    elif s == 'reuters':
        return dateparser.parse(''.join(soup.find('div', attrs={'class': 'ArticleHeader_date_V9eGk'}).text.strip().split('/')[:2]), fuzzy=True)
    
    # module not specialized in source, need to account for errors
    # try:
    # except:
    return None

def find_article(soup, source, container):
    s, c = source.lower(), container.lower()
    offset = 0 
    if s == 'bloomberg': offset = 8
    return ' '.join(list(map(lambda p: p.text.strip(), soup.find_all('p')[offset:]))).encode('utf-8')


def crawl_home_page(soup, ID):
    ID = ID.lower()
    if ID == 'quote':       # bloomberg
        return list(map(lambda url: url['href'], soup.find_all('a', attrs={'class': 'news-story__url'}, href=True)))        
    elif ID == 'symbol':  # seeking alpha
        base = 'https://seekingalpha.com'
        return list(map(lambda url: base + url['href'],soup.find_all('a', attrs={'sasource': 'qp_latest'}, href=True)))  
    elif ID == 'finance':   # reuters
        base = 'http://reuters.com'
        return list(map(lambda url: base + url['href'], soup.find('div', attrs={'id': 'companyOverviewNews'}).find_all('a')))  
    return None


def scrape(url, source, curious=False, ticker=None):
    url_obj = urlparse(url)
    if not url_obj: return None
    if not validate_url(url_obj, source, curious=curious): return None
    print('URL has been validated and accepted')
    
    try: 
        article_req = requests.get(url)
        article_req.raise_for_status()
    except requests.exceptions.RequestException as e:
        print('Web Scraper Error: {}'.format(str(e)))
        return None

    paths = url_obj.path.split('/')[1:] # first entry is '' so exclude it

    soup = BS(article_req.content, 'html.parser')
    p = paths[0].lower()
    if p in ['quote', 'symbol', 'finance']: return crawl_home_page(soup, p)
   
    pubdate = find_date(soup, source, paths[0])
    article = find_article(soup, source, paths[0])
    
    # if len(article) < 30: return None

    print('found pubdate to be: {}'.format(str(pubdate)))
    # print('found article to be: {}'.format(article))

    words = article.decode('utf-8').split(u' ')
    sentences = list(map(lambda s: s.encode('utf-8'), re.split(r' *[\.\?!][\'"\)\]]* *', article.decode('utf-8'))))

    # if ticker:
    #     google_url = 'https://www.google.com/finance?&q='+ticker
    #     try: 
    #         google_req = requests.get(google_url)
    #         google_req.raise_for_status()
    #     except requests.exceptions.RequestException as e:
    #         print('Web Scraper Error from google_url: {}'.format(str(e)))
    #         return None
    #     s = soup(google_req.content, 'html.parser')
    #     x = s.find_all('a', attrs={'class':'sector'})
    #     html = re.findall(r'Sector: (.*?) ', google_req.content, re.DOTALL)

    return WebNode(pubdate, article, words, sentences)




# url = 'https://www.bloomberg.com/press-releases/2017-07-13/top-5-companies-in-the-global-consumer-electronics-and-telecom-products-market-by-bizvibe'
# url = 'https://www.bloomberg.com/gadfly/articles/2017-04-27/under-armour-earnings-buckle-up'
# url = 'https://www.bloomberg.com/news/videos/2017-04-27/under-armour-regains-footing-amid-footwear-slump-video'
# url = 'https://www.bloomberg.com/quote/UA:US'
url = 'https://www.bloomberg.com/news/articles/2017-04-27/under-armour-loses-whatever-swagger-it-had-left'
print (scrape(url, 'bloomberg', ticker='ua'))
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




# def main():
#     """ this module returns either a Node, list of urls or None"""

# if __name__ == "__main__":
#     main()




