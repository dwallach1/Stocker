from __future__ import unicode_literals, print_function
import os
import logging
import json 
import random
import time
import csv 
import re
from bs4 import BeautifulSoup 
from tqdm import tqdm, trange

from RequestService import RequestHandler
from FinanceService import FinanceHelper
from ArticleService import ArticleParser
import utility 

logger = logging.getLogger(__name__)
                    
class Stocker(object):
    """stocker class manages the work for mining data and writing it to disk"""
    
    def __init__(self, tickers, sources, csv_path, json_path, stats_path=None, verbose=True):
        self.tickers = tickers
        self.sources = sources
        self.csv_path = csv_path
        self.json_path = json_path
        self.stats_path = stats_path
        self.queries = []
        self.requestHandler = RequestHandler()
        self.financeHelper = FinanceHelper()
        self.verbose = verbose

    def build_queries(self, depth=1):
        """creates google queries based on the provided stocks and news sources"""
        i, j = 0, '.'
        tot = len(self.tickers) * len(self.sources) * depth
        for t in self.tickers:
            for s in self.sources:
                if self.verbose: 
                    utility.sysprint('Building {} out of {} queries | {} {} done'.format(i, tot, (i / tot), '%'))
                i += 1
                string1 = t + '+' + s + '+' + 'stock+articles'
                if depth > 1:
                    company_name = self.financeHelper.get_name_from_ticker(t) 
                    if company_name:
                        garbage = ['Inc.']
                        string2 =  '+'.join([j for j in company_name.split(' ') if j not in garbage]) + '+' + s + '+stock+news'
                        self.queries.append(Query(t, s, string2))
                        i += 1
                self.queries.append(utility.Query(t, s, string1))
        logger.debug('built {} queries'.format(len(self.queries)))

    def stock(self, gui=True, json_output=True, csv_output=True, depth=1, query=True, shuffle=False, flags={}):
        """main function for the class. Begins the worker to get the information based on the queries given"""
        if query: 
            self.build_queries(depth=depth)
        if shuffle: 
            random.shuffle(self.queries) # shuffule the queries to try to limit bot detection
        total = len(self.queries)
        if total == 0: 
            return None
        
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
            if self.verbose: 
                utility.sysprint('Processing query: {}'.format(curr_q.string))
            logger.debug('Processing query: {}'.format(curr_q.string))
            
            if gui:
                t.set_description(curr_q.ticker.upper())
                t.set_postfix(source=curr_q.source)
                t.update()

            urls = self.get_urls(curr_q, json_output)
            if self.stats_path:  
                urls_found = len(urls)
            logger.debug('urls are {}'.format(json.dumps(urls, indent=4)))
            
            nodes, urls, extra = self.build_nodes(curr_q, urls, flags=flags)
            
            if self.stats_path: 
                urls_found += extra

            node_dict = [dict(node) for node in nodes] if (not nodes) else None
            if self.stats_path: 
                self.update_stocker_stats(urls_found, curr_q.source, len(node_dict))
            
            if node_dict == None or len(node_dict) == 0: continue
            
            if not node_dict is None:
                if csv_output:     self.write_csv(node_dict, curr_q)
                if json_output:    self.write_json(urls, curr_q.ticker)
        
                print('\n\nFished gathering data, preparing to exit.')
        if gui: t.close()
        return nodes
        
    def get_urls(self, query, json_output):
        """searches the query in google and returns the resulting urls"""
        url = 'https://www.google.co.in/search?site=&source=hp&q={}&gws_rd=ssl'.format(query.string)
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error getting URL: {} due to err: {}'.format(url, err))
            return None

        soup = BeautifulSoup(resp.content,'html.parser')
        # reg = re.compile('.*&sa=')
        new_urls = []
        for item in soup.find_all('div', attrs={'class' : 'g'}): 
            url = item.a['href'][7:] # offset to get rid of <a href=
            if url:
                if url[0] == '/': url = url[1:]
                if url[:4] != 'http': url = 'http://' + url # attach web protocol, if not there -- default to http
                new_urls.append(url) 
        
        logger.debug('found {} links from the query'.format(len(new_urls)))
        if not json_output: 
            return new_urls
        return self.remove_dups(new_urls, query.ticker)
    
    def remove_dups(self, urls, ticker):
        """removes already parsed urls from those found by get_urls"""
        if not os.path.exists(self.json_path): 
            return urls
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        parsed_urls = data[ticker] if ticker in data else []
        return [url for url in urls if not (url in parsed_urls)]    

    def build_nodes(self, query, urls, flags):
        """uses the urls to build WebNodes to be written to the csv output"""
        if len(urls) == 0: 
            return None, []
        nodes = []
        extra = 0
        j = '.'
        for i, url in enumerate(urls):
            if self.verbose: 
                utility.sysprint('parsing urls for query: {}'.format(query.string) + j*(i % 3))
            
            articleParser = ArticleParser(url, source, **flags)
            node = articleParser.generate_web_node()
            # node = scrape(url, query.source, ticker=query.ticker, **flags)
            
            if isinstance(node, list):
                for url in node:
                    if not (url in urls):
                        urls.append(url)
                        extra += 1
                logger.debug('Hit landing page -- crawling for more links')
            elif node != None: 
                nodes.append(node)
            else: 
                urls.remove(url)
        if self.verbose: 
            utility.sysprint ('built {} nodes to write to disk'.format(len(nodes)))
        logger.debug('built {} nodes to write to disk'.format(len(nodes)))
        return nodes, urls, extra

    def write_csv(self, node_dict, query):
        """writes the data gathered to a csv file"""
        if self.verbose: 
            utility.sysprint('writing {} node(s) to csv'.format(len(node_dict)))
        logger.debug('writing {} node(s) to csv for query {}'.format(len(node_dict), query))
       
        write_mode = 'a' if os.path.exists(self.csv_path) else 'w' 
        with open(self.csv_path, write_mode) as f:
            fieldnames = node_dict[0].keys() # sort to ensure they are the same order every time
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_mode == 'w':
                writer.writeheader()
            writer.writerows(node_dict)

    def write_json(self, urls, ticker):
        """writes parsed links to JSON file to avoid reparsing"""
        if self.verbose: 
            utility.sysprint('writing {} link(s) to json'.format(len(urls)))
        logger.debug('writing {} link(s) to json'.format(len(urls)))
        
        t = ticker.upper()
        write_mode = 'r' if os.path.exists(self.json_path) else 'w' 
        with open(self.json_path, write_mode) as f:
            if write_mode == 'w': 
                data = {}
            else: 
                data = json.load(f)
        
        # TODO : Build a is_homepage function to be used here
        # remove homepages b/c we want to parse again
        # urls = filter(lambda url: not (urlparse(url).path.split('/')[1].lower() in homepages()),
        #        filter(lambda url: url[:4] == 'http', urls)) 

        # add urls to json
        if t in data.keys():
            original = data[t] 
            updated = original + urls 
            data.update({t : updated})
        else: 
            data.update({t : urls})

        with open(self.json_path, 'w') as f: 
            json.dump(data, f, indent=4)

    def update_stocker_stats(self, num_urls, source, num_nodes):
        if self.verbose: 
            utility.sysprint('updating stocker_stats.json')
        logger.debug('updating stocker_stats.json')
        
        write_mode = 'r' if os.path.exists(self.stats_path) else 'w' 
        with open(self.stats_path, write_mode) as f:
            if write_mode == 'w': 
                data = {}
            else: 
                data = json.load(f)

        # add urls to json
        if source in data.keys():
            original = data[source] 

            # error occuring here
            updated = {}
            updated['num_urls'] = original['num_urls'] + num_urls
            updated['num_nodes'] = original['num_nodes'] + num_nodes
            data.update({source : updated})
        else: data.update({ source : {
                            'num_urls': num_urls,
                            'num_nodes': num_nodes
                    }
            })

        #write the updated json
        with open(self.stats_path, 'w') as f: 
            json.dump(data, f, indent=4)
    