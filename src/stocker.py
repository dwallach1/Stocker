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
import random
import time, csv, re
from urlparse import urlparse
import requests
from bs4 import BeautifulSoup as BS
from tqdm import tqdm, trange
from datetime import datetime
from webparser import scrape, homepages

logger = logging.getLogger(__name__)

printer = True

class Loading:
    busy = False
    def loading(self, text):
        while self.busy:
            sys.stdout.write('{}   \r'.format(text))
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('{}.  \r'.format(text))
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('{}.. \r'.format(text))
            sys.stdout.flush()
            time.sleep(1)
            sys.stdout.write('{}...\r'.format(text))
            sys.stdout.flush()
            time.sleep(1)

    def start(self, text):
        self.busy = True
        threading.Thread(target=self.loading, kwargs={'text':text}).start()

    def stop(self):
        self.busy = False
        time.sleep(1)

def sysprint(text):
    sys.stdout.flush()
    sys.stdout.write('{}\r'.format(text))
    sys.stdout.flush()
    

def SNP_500():
    if printer:
        loader = Loading()
        loader.start('Loading SNP500')
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers)
    except: return None
    soup = BS(req.content, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) > 0:
            ticker = str(col[0].string.strip())
            tickers.append(ticker)
    if printer: loader.stop()
    return tickers

def NYSE_Top100():
    if printer: 
        loader = Loading()
        loader.start('Loading NYSE100')
    url = 'http://online.wsj.com/mdc/public/page/2_3021-activnyse-actives.html'
    try:
        req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        req.raise_for_status()
    except: return None
    soup = BS(req.content, 'html.parser')
    if printer: loader.stop()
    return map(lambda stock: re.findall(r'\(.*?\)', stock.text)[0][1:-1], soup.find_all('td', attrs={'class': 'text'}))

def NASDAQ_Top100():
    if printer:
        loader = Loading()
        loader.start('Loading NASDAQ100')
    url = 'http://online.wsj.com/mdc/public/page/2_3021-activnnm-actives.html'
    try:
        req = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        req.raise_for_status()
    except: return None
    soup = BS(req.content, 'html.parser')
    if printer: loader.stop()
    return map(lambda stock: re.findall(r'\(.*?\)', stock.text)[0][1:-1], soup.find_all('td', attrs={'class': 'text'}))

def valid_sources(): return ['bloomberg', 'seekingalpha', 'reuters', 'thestreet', 'investopedia']
def querify(string): return '+'.join(string.split(' '))

class Query(object):
    def __init__(self, ticker, source, string):
        self.ticker = ticker
        self.source = source
        self.string = string
           
              
class Stocker(object):
    """stocker class manages the work for mining data and writing it to a csv file"""
    def __init__(self, tickers, sources, csv_path, json_path):
        self.tickers = tickers
        self.sources = sources
        self.csv_path = csv_path
        self.json_path = json_path
        self.queries = []

    def build_queries(self, depth=1):
        """creates google queries based on the provided stocks and news sources"""
        if printer:
            loader = Loading()
            loader.start('Building queries')
        for t in self.tickers:
            for s in self.sources:
                string1 = t + '+' + s + '+' + 'stock+articles'
                if depth > 1:
                    cname = self.get_name(t) 
                    if not (cname is None):
                        string2 =  '+'.join(map(lambda name: re.sub(r'[^\w\s]','',name), filter(lambda i: i != 'Inc.' ,cname.split(' ')))) + '+' + s + '+stock+news'
                        self.queries.append(Query(t, s, string2))
                self.queries.append(Query(t, s, string1))
        if printer: loader.stop()
        logger.debug('built {} queries'.format(len(self.queries)))

    def stock(self, gui=True, nodes=False, json=True, csv=True, depth=1, query=True, shuffle=True):
        """main function for the class. Begins the worker to get the information based on the queries given"""
        if query: self.build_queries(depth=depth)
        if shuffle: random.shuffle(self.queries)
        total = len(self.queries)
        if total == 0: return None
        if gui: t = trange(total, total=total, unit='query', desc=self.queries[0].ticker, postfix={'source':self.queries[0].source},
                                                                                dynamic_ncols=True, leave=True, miniters=1)
        else: t = range(total) 
        for i in t:
            q = self.queries[i]
            #_ticker, _source, _query = q.ticker, q.source, q.string 
            if printer: sysprint('Processing query: {}'.format(q.string))
            logger.debug('Processing query: {}'.format(q.string))
            if gui:
                t.set_description(q.ticker.upper())
                t.set_postfix(source=q.source)
                t.update()
            
            worker = Worker(q.ticker, q.source, q.string)
            worker.get_urls()
            worker.remove_dups(self.json_path)
            worker.build_nodes()
            node_dict = worker.dictify()
            if not (node_dict is None):
                if csv:     self.write_csv(node_dict)
                if json:    self.write_json(worker.urls, worker.ticker)
        if gui: t.close()
        if nodes: return worker.nodes
        print('\nDone.')

    def write_csv(self, node_dict):
        """writes the data gathered to a csv file"""
        if printer: sysprint('writing {} nodes to csv'.format(len(node_dict)))
        logger.debug('writing {} nodes to csv '.format(len(node_dict)))
        write_mode = 'a' if os.path.exists(self.csv_path) else 'w'
        with open(self.csv_path, write_mode) as f:
            fieldnames = sorted(node_dict[0].keys()) # sort to ensure they are the same order every time
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_mode == 'w':
                writer.writeheader()
            writer.writerows(node_dict)

    def write_json(self, urls, ticker):
        """writes parsed links to JSON file to avoid reparsing"""
        if printer: sysprint('writing {} links to csv'.format(len(urls)))
        logger.debug('writing {} links to csv'.format(len(urls)))
        write_mode = 'r' if os.path.exists(self.json_path) else 'w' 
        t = ticker.upper()
        with open(self.json_path, write_mode) as f:
            if write_mode == 'w': data = {}
            else: data = json.load(f)
        
        # remove homepages
        urls = filter(lambda url: not (urlparse(url).path.split('/')[1].lower() in homepages()),
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
        """convert the ticker to the associated company name"""
        url = 'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query='+ticker.upper()+'&region=1&lang=en'
        # headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            result = requests.get(url, headers=headers).json()
            result.raise_for_status()
        except: return None

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

    def __str__(self): return self.query

    # def __repr__(self):
    # def __eq__(self):

    def remove_dups(self, json_path):
        if not os.path.exists(json_path): return 
        with open(json_path, 'r') as f:
            data = json.load(f)
        parsed_urls = data[self.ticker] if self.ticker in data else []
        self.urls = filter(lambda url: not(url in parsed_urls), self.urls)

    def get_urls(self):
        _url = 'https://www.google.co.in/search?site=&source=hp&q='+self.query+'&gws_rd=ssl'
        try:
            time.sleep(15)
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
        self.urls = new_urls

    def build_nodes(self):
        j = '.'
        for i, url in enumerate(self.urls):
            if printer: sysprint('parsing urls for query: {}'.format(self.query) + j*(i+1 % 3))
            node = scrape(url, self.source, ticker=self.ticker)
            if isinstance(node, list):
                self.urls += filter(lambda url: not(url in self.urls), node)
                logger.debug('Hit landing page -- crawling for more links')
            elif node != None: self.nodes.append(node)
            else: self.urls.remove(url)
        if printer: sysprint ('built {} nodes to write to disk'.format(len(self.nodes)))
        logger.debug('built {} nodes to write to disk'.format(len(self.nodes)))

    def dictify(self): 
        if len(self.nodes) == 0: return None 
        return list(map(lambda node: {  'ticker': self.ticker,
                                        'sector': node.sector,
                                        'industry': node.industry,
                                        'article': node.article,
                                        'url': node.url,
                                        'pubdate': node.pubdate,
                                        'class': node.classification 
                                        }, self.nodes))
