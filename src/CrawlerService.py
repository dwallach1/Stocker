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
        print ()

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
            logger.debug('urls are {}'.format(json.dumps(urls, indent=4)))
            if self.stats_path:  
                urls_found = len(urls)
            
            nodes = self.build_nodes(curr_q, urls, flags=flags)
            
            node_dict = [dict(node) for node in nodes] if (not nodes) else None
            
            if self.stats_path: 
                logger.debug('stats_path ({}) is set, updating statistics'.format(self.stats_path))
                num_nodes = len(node_dict) if node_dict else 0
                self.update_stocker_stats(urls_found, curr_q.source, num_nodes)
            
            if node_dict == None or len(node_dict) == 0: 
                logger.debug('Node Dictionary is None or has a length of 0, continuing to next iteration.')
                continue
            
            if not node_dict is None:
                if self.csv_path:   
                    logger.debug('csv_path ({}) is set, writitng node_dict to disk'.format(self.csv_path))  
                    self.write_csv(node_dict, curr_q)
                if self.json_path:   
                    logger.debug('json_path ({}) is set, writitng node_dict to disk'.format(self.json_path))  
                    self.write_json(urls, curr_q.ticker)
                
                print('\n\nFished gathering data, preparing to exit.')
        utility.sysprint('Done.')
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
        
        new_urls = [url for url in new_urls if self.is_of_source(url, query.source)]
        logger.debug('found {} links from the query'.format(len(new_urls)))
        if not json_output: 
            return new_urls
        return self.remove_dups(new_urls, query.ticker)
    
    def remove_dups(self, urls, ticker):
        """removes already parsed urls from those found by get_urls"""
        logger.debug('removing duplicate links')
        if not os.path.exists(self.json_path): 
            logger.warn('tryed to remove duplicate links, but json_path ({}) did not exist'.format(self.json_path))
            return urls
        logger.debug('opening file at json path: {}'.format(self.json_path))
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        parsed_urls = data[ticker] if ticker in data else []
        return [url for url in urls if not (url in parsed_urls)]    

    def build_nodes(self, query, urls, flags):
        """uses the urls to build WebNodes to be written to the csv output"""
        nodes = []
        extra = 0
        if len(urls) == 0: 
            return nodes, urls, extra
        j = '.'
        for i, url in enumerate(urls):
            if self.verbose: 
                utility.sysprint('parsing urls for query: {}'.format(query.string) + j*(i % 3))
            
            if self.is_homepage(url, query.source):
                logger.debug('Hit a homepage ({}) ... continuing to next iteration.'.format(url))
                continue

            articleParser = ArticleParser(url, query.source, **flags)
            node = articleParser.generate_web_node()
            nodes.append(node)
            
        if self.verbose: 
            utility.sysprint ('built {} Web Nodes'.format(len(nodes)))
        logger.debug('built {} Web Nodes'.format(len(nodes)))
        return nodes

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
    
    def is_homepage(self, url, source):
        """ """
        regex_map = {
            'bloomberg': r'bloomberg\.com\/quote\/[a-zA-Z]*:[a-zA-Z]*',
            'yahoo':     r'finance\.yahoo\.com\/quote\/(.?)'
        }
        return bool(re.compile(regex_map[source]).search(url))

    def is_of_source(self, url, source):
        """ """
        SOURCE_REGEX = r'www\.(.*)\.com'
        match = re.search(SOURCE_REGEX, url, re.IGNORECASE)
        if not match: 
            logger.warn('Unable to find a match to test if valid source... Returning False blindly.')
            return False
        res = (source == match.group(1))
        if not res:
            logger.debug('url: {} was found to be of an incorrect source (expected: {}, found: {})... filtering out url.'.format(url, source, match.group(1)))
        return res