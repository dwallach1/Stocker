from __future__ import print_function
"""
stocker.py
Author: David Wallach

- Uses BeautifulSoup for scraping the data from URLs

This Python module has several purposes oriented around mining data from the web.
The functionality is comprised of gathering urls from google quereis and then getting the data from 
those articles such as the article body and publishing date
"""
import os, sys, logging, json, string
import threading, time
import time, csv, re
from urlparse import urlparse
import requests
from bs4 import BeautifulSoup as BS
from tqdm import tqdm, trange
from datetime import datetime
from webparser import scrape

logger = logging.getLogger(__name__)


# TODO: get cname -- breaks -- client errors -- change headerss
# TODO: make sure client 403 errors are not happening (ensure web headers are valid)
# TOD0: take out homepages from parsed urls         [done]
# TODO: add multiple queries 
# TODO: add sector and industry                     [done]
# TODO: add error handling to all http requests
# TODO: add investopedia and thestreet to known sources

class Loading:
    busy = False
    def loading_snp(self):
        while self.busy:
            sys.stdout.write('Getting S&P500 Stocks   \r')
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('Getting S&P500 Stocks.  \r')
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('Getting S&P500 Stocks.. \r')
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('Getting S&P500 Stocks...\r')
            sys.stdout.flush()
            time.sleep(1)

    def start(self):
        self.busy = True
        threading.Thread(target=self.loading_snp).start()

    def stop(self):
        self.busy = False
        time.sleep(1)

def snp_500():
    # loader = Loading()
    # loader.start()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    req = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers)
    soup = BS(req.content, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) > 0:
            ticker = str(col[0].string.strip())
            tickers.append(ticker)
    # loader.stop()
    return tickers

def valid_sources(): return ['bloomberg', 'seekingalpha', 'reuters', 'thestreet', 'investopedia']

class Stocker(object):
    """stocker class manages the work for mining data and writing it to a csv file"""
    def __init__(self, tickers, sources, csv_path, json_path):
        self.tickers = tickers
        self.sources = sources
        self.csv_path = csv_path
        self.json_path = json_path
        self.queries = []

    def build_queries(self, depth=1):
        for t in self.tickers:
            for s in self.sources:
                q1 = t + '+' + s + '+' + 'stock+articles'
                if depth > 1:
                    cname = self.get_name(t) 
                    if not (cname is None):
                        q2 = s + '+' + '+'.join(map(lambda s: re.sub(r'[^\w\s]','',s), filter(lambda i: i != 'Inc.' ,cname.split(' ')))) + '+news'
                        self.queries.append([t, s, q2])
                self.queries.append([t, s, q1])
        logger.debug('built {} queries'.format(len(self.queries)))

    def stock(self, gui=True):
        self.build_queries()
        total = len(self.queries)
        if gui: t = trange(len(self.queries), total=total, unit='query', desc='Configuring',dynamic_ncols=True, 
                                                                                leave=True, miniters=1)
        else: t = range(len(self.queries)) 
        for i in t:
            q = self.queries[i]
            if gui:
                t.set_description(q[0].upper())
                t.set_postfix(source=q[1])
                t.update()
            
            worker = Worker(q[0], q[1], q[2])
            worker.configure(self.json_path)
            worker.work()
            node_dict = worker.dictify()
            if not (node_dict is None): 
                self.write_csv(node_dict)
                self.write_json(worker.urls, worker.ticker)
        if gui:
            t.close()
        print('\nDone.')

    def write_csv(self, node_dict):
        # node_dict = list(map(lambda n: n.dictify(), list(filter(lambda n: n.date != None , nodes))))
        write_mode = 'a' if os.path.exists(self.csv_path) else 'w'
        with open(self.csv_path, write_mode) as f:
            fieldnames = sorted(node_dict[0].keys()) # sort to ensure they are the same order every time
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_mode == 'w':
                writer.writeheader()
            writer.writerows(node_dict)

    def write_json(self, urls, ticker):
        write_mode = 'r' if os.path.exists(self.json_path) else 'w' 
        t = ticker.upper()
        with open(self.json_path, write_mode) as f:
            if write_mode == 'w': data = {}
            else: data = json.load(f)
        
        # remove homepages
        urls = filter(lambda url: not (urlparse(url).path.split('/')[1].lower() in ['quote', 'symbol', 'finance']),
               filter(lambda url: url[:4] == 'http', urls)) 

        # add urls to json
        if t in data.keys():
            original = data[t] 
            updated = original + urls 
            data.update({t : updated})
        else:
            data.update({t : urls})

        #write the updated json
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_name(self, ticker):
        """
        Convert the ticker to the associated company name
        """
        url = 'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en'.format(ticker)
        headers = {'User-Agent': 'Mozilla/5.0'}
        result = requests.get(url).json()

        for x in result['ResultSet']['Result']:
            if x['symbol'] == ticker:
                return x['name']

class Worker(object):
    """contains the work of the program, filling in the node data so that it can be written to the csv file"""
    def __init__(self, ticker, source, query):
        self.ticker = ticker.upper()    # string
        self.source = source            # string
        self.query = query              # string
        self.urls = []                  # array (string)
        self.nodes = []                 # array (WebNode())

    def configure(self, json_path):
        if not os.path.exists(json_path): return 
        with open(json_path, 'r') as f:
            data = json.load(f)
        self.urls = data[self.ticker] if self.ticker in data else []
        logger.debug('configuring urls with a length of {}'.format(len(self.urls)))

    def work(self):
        self.get_urls()
        self.build_nodes()

    def get_urls(self):
        _url = 'https://www.google.co.in/search?site=&source=hp&q='+self.query+'&gws_rd=ssl'
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = requests.get(_url, headers=headers)
            req.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error('error {} occurred in function set_urls'.format(str(e))) 
            return 

        soup = BS(req.content,'html.parser')
        
        reg=re.compile('.*&sa=')
        new_urls = []
        for item in soup.find_all(attrs={'class' : 'g'}): new_urls.append(reg.match(item.a['href'][7:]).group()[:-4])
        self.urls = self.urls + list(set(new_urls) - set(self.urls))
        #list(filter(lambda url: url not in self.urls, urls))

    def build_nodes(self):
        for url in self.urls:
            node = scrape(url, self.source, ticker=self.ticker)
            if isinstance(node, list):
                self.urls = self.urls + list(set(node) - set(self.urls))
                logger.debug('Hit landing page -- crawling for more links')
                continue
            elif node != None: self.nodes.append(node)
            else: self.urls.remove(url)
        logger.debug('built {} nodes'.format(len(self.nodes)))

    def dictify(self): 
        if len(self.nodes) == 0: return None 
        return list(map(lambda node: {  'ticker': self.ticker,
                                        'sector': node.sector,
                                        'industry': node.industry,
                                        # 'article': node.article,
                                        'url': node.url,
                                        'pubdate': node.pubdate,
                                        # 'sentences': node.sentences,
                                        # 'words': node.words,
                                        'polarity': node.polarity,
                                        'subjectivity': node.subjectivity,
                                        'negative': node.negative,
                                        'positive': node.positive,
                                        'priceT0': 0.0,
                                        'priceT1': 0.0,
                                        'Class': 0 }, self.nodes))
