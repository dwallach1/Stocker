from __future__ import unicode_literals, print_function
"""
stocker.py
Author: David Wallach

This Python module has several purposes oriented around mining data from the web.
The functionality is comprised of gathering urls from google queries, parsing the information, such as the article body 
and publishing date, and then returning WebNodes with the found data. WebNodes are configured based on the parameters that 
the main stocker function is called with. 
"""
import os, sys, logging, json, string
import random, time, csv, re
from collections import namedtuple
from urlparse import urlparse
import requests
from datetime import datetime
from bs4 import BeautifulSoup 
from tqdm import tqdm, trange
from webparser import scrape, RequestHandler, homepages

logger = logging.getLogger(__name__)
printer = True
Query = namedtuple('Query', 'ticker source string')
                    
class Stocker(object):
    """stocker class manages the work for mining data and writing it to disk"""
    requestHandler = RequestHandler()
    def __init__(self, tickers, sources, csv_path, json_path):
        self.tickers = tickers
        self.sources = sources
        self.csv_path = csv_path
        self.json_path = json_path
        self.queries = []

    def build_queries(self, depth=1):
        """creates google queries based on the provided stocks and news sources"""
        i, j = 0, '.'
        for t in self.tickers:
            for s in self.sources:
                if printer: sysprint('Building queries' + j*(i % 3))
                i += 1
                string1 = t + '+' + s + '+' + 'stock+articles'
                if depth > 1:
                    cname = self.get_name(t) 
                    if not (cname is None):
                        string2 =  '+'.join(map(lambda name: re.sub(r'[^\w\s]','',name), filter(lambda i: i != 'Inc.' ,cname.split(' ')))) + '+' + s + '+stock+news'
                        self.queries.append(Query(t, s, string2))
                self.queries.append(Query(t, s, string1))
        logger.debug('built {} queries'.format(len(self.queries)))

    def get_name(self, ticker):
        """convert the ticker to the associated company name"""
        url = 'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en'.format(ticker.upper())
        req = self.requestHandler.get(url)
        if req == None: return None
        req = req.json()

        for data in req['ResultSet']['Result']:
            if data['symbol'] == ticker:
                return data['name']

    def stock(self, gui=True, json=True, csv=True, depth=1, query=True, shuffle=True, flags={}):
        """main function for the class. Begins the worker to get the information based on the queries given"""
        if query: self.build_queries(depth=depth)
        if shuffle: random.shuffle(self.queries)
        total = len(self.queries)
        if total == 0: return None
        trange_args = { 'total':            total, 
                        'unit':             'query', 
                        'desc':             self.queries[0].ticker, 
                        'postfix':          {'source':self.queries[0].source},
                        'dynamic_ncols':    True, 
                        'leave':            True, 
                        'miniters':         1
                        }
        if gui: t = trange(total, **trange_args)
        else: t = range(total) 
        for i in t:
            curr_q = self.queries[i]
            if printer: sysprint('Processing query: {}'.format(curr_q.string))
            logger.debug('Processing query: {}'.format(curr_q.string))
            if gui:
                t.set_description(curr_q.ticker.upper())
                t.set_postfix(source=curr_q.source)
                t.update()

            urls = self.get_urls(curr_q, json)
            nodes, urls = self.build_nodes(curr_q, urls, flags=flags)
            node_dict = None
            if not(nodes == None): node_dict = [dict(node) for node in nodes]

            if not (node_dict is None):
                if csv:     self.write_csv(node_dict)
                if json:    self.write_json(urls, curr_q.ticker)
        print('\nDone.')
        if gui: t.close()
        return nodes
        
    def get_urls(self, query, json):
        """searches the query in google and returns the resulting urls"""
        url = 'https://www.google.co.in/search?site=&source=hp&q={}&gws_rd=ssl'.format(query.string)
        req = self.requestHandler.get(url)
        if req == None: return None

        soup = BeautifulSoup(req.content,'html.parser')
        reg = re.compile('.*&sa=')
        new_urls = []
        for item in soup.find_all(attrs={'class' : 'g'}): new_urls.append(reg.match(item.a['href'][7:]).group()[:-4])
        logger.debug('found {} links from the query'.format(len(new_urls)))
        if not json: return new_urls
        return self.remove_dups(new_urls, query.ticker)
    
    def remove_dups(self, urls, ticker):
        """removes already parsed urls from those found by get_urls"""
        if not os.path.exists(self.json_path): return urls
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        parsed_urls = data[ticker] if ticker in data else []
        return [url for url in urls if not (url in parsed_urls)]    

    def build_nodes(self, query, urls, flags):
        """uses the urls to build WebNodes to be written to the csv output"""
        if len(urls) == 0: return None, []
        nodes = []
        j = '.'
        for i, url in enumerate(urls):
            if printer: sysprint('parsing urls for query: {}'.format(query.string) + j*(i % 3))
            node = scrape(url, query.source, ticker=query.ticker, **flags)
            if isinstance(node, list):
                urls += [url for url in node if not(url in urls)]
                logger.debug('Hit landing page -- crawling for more links')
            elif node != None: nodes.append(node)
            else: urls.remove(url)
        if printer: sysprint ('built {} nodes to write to disk'.format(len(nodes)))
        logger.debug('built {} nodes to write to disk'.format(len(nodes)))
        return nodes, urls

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
        
        # remove homepages b/c we want to parse again
        urls = filter(lambda url: not (urlparse(url).path.split('/')[1].lower() in homepages()),
               filter(lambda url: url[:4] == 'http', urls)) 

        # add urls to json
        if t in data.keys():
            original = data[t] 
            updated = original + urls 
            data.update({t : updated})
        else: data.update({t : urls})

        #write the updated json
        with open(self.json_path, 'w') as f: 
            json.dump(data, f, indent=4)

    
# -----------------------
#
#   EXTERNAL FUNCTIONS
#
# -----------------------

def sysprint(text):
    sys.stdout.write('\r{}\033[K'.format(text))
    sys.stdout.flush()

def moveup(lines):
    for _ in range(lines):
        sys.stdout.write("\x1b[A")

def SNP_500():
    if printer: sysprint('Loading SNP500')
    url = 'http://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    req = RequestHandler().get(url)
    if req == None: return 
    soup = BeautifulSoup(req.content, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) > 0:
            ticker = str(col[0].string.strip())
            tickers.append(ticker)
    if printer: sysprint('Finished loading SNP500')
    return tickers

def NYSE_Top100():
    if printer: sysprint('Loading NYSE100')
    url = 'http://online.wsj.com/mdc/public/page/2_3021-activnyse-actives.html'
    req = RequestHandler().get(url)
    if req == None: return None
    soup = BeautifulSoup(req.content, 'html.parser')
    if printer: sysprint('Finished loading NYSE100')
    return map(lambda stock: re.findall(r'\(.*?\)', stock.text)[0][1:-1], soup.find_all('td', attrs={'class': 'text'}))

def NASDAQ_Top100():
    if printer: sysprint('Loading NASDAQ100')
    url = 'http://online.wsj.com/mdc/public/page/2_3021-activnnm-actives.html'
    req = RequestHandler().get(url)
    if req == None: return None
    soup = BeautifulSoup(req.content, 'html.parser')
    if printer: sysprint('Finished loading NASDAQ100')
    return map(lambda stock: re.findall(r'\(.*?\)', stock.text)[0][1:-1], soup.find_all('td', attrs={'class': 'text'}))

def valid_sources(): return ['bloomberg', 'seekingalpha', 'reuters', 'thestreet', 'investopedia']
def querify(ticker, source, string): return Query(ticker, source, '+'.join(string.split(' ')))

def googler(string):
    url = 'https://www.google.com/search?site=&source=hp&q={}&gws_rd=ssl'.format('+'.join(string))
    req = RequestHandler().get(url)
    if req == None: return []
    soup = BeautifulSoup(req.content,'html.parser')  
    reg=re.compile('.*&sa=')
    urls = []
    for item in soup.find_all(attrs={'class' : 'g'}): urls.append(reg.match(item.a['href'][7:]).group()[:-4])
    return urls

def earnings_watcher():
    """ returns a list of tickers of which their earning's reports are scheduled to release today (if weekday)"""
    url = 'https://www.bloomberg.com/markets/earnings-calendar/us'
    pass
