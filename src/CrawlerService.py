from __future__ import unicode_literals, print_function
import os
import subprocess
import logging
import json 
import time
import re
from bs4 import BeautifulSoup 
from tqdm import tqdm, trange

from RequestService import RequestHandler
from FinanceService import FinanceHelper
from ArticleService import ArticleParser
from QualtricsService import QualtricsHandler
import UtilityService as utility

logger = logging.getLogger(__name__)
                    
class Stocker(object):
    """stocker class manages the work for mining data and writing it to disk"""
    
    def __init__(self, tickers, sources, configpath, verbose=True):
        self.tickers = tickers
        self.sources = sources

        file_path = os.path.dirname(os.path.abspath(__file__))
        proj_dir = os.path.dirname ( file_path )
        data_dir_path = proj_dir + '/data/' 
        if not os.path.isdir(data_dir_path):
            initalize_cmd = subprocess.Popen(['make', 'clean'], 
                                                stdout=subprocess.PIPE, 
                                                stderr=subprocess.STDOUT)
            initalize_cmd.communicate()

        self.data_file = data_dir_path + 'data.json'
        self.url_file = data_dir_path + 'urls.json'
        self.stats_file = data_dir_path + 'stats.json'
        self.queries = []
        self.use_qualtrics = bool(configpath)
        if self.use_qualtrics:
            with open(configpath, 'r') as f:
                secrets = json.load(f)
            self.qualtricsHandler = QualtricsHandler(secrets['Q_TOKEN'], secrets['Q_DATACENTER'], secrets['Q_SURVEY_ID'])
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
                        self.queries.append(utility.Query(t, s, string2))
                        i += 1
                self.queries.append(utility.Query(t, s, string1))
        logger.debug('built {} queries'.format(len(self.queries)))

    def stock(self, gui=True, json_output=True, csv_output=True, depth=1, query=True, shuffle=False, flags={}):
        """main function for the class. Begins the worker to get the information based on the queries given"""
        if query: 
            self.build_queries(depth=depth)
        
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
            query = self.queries[i]
            if self.verbose: 
                utility.sysprint('Processing query: {}'.format(query.string))
            logger.debug('Processing query: {}'.format(query.string))
            
            if gui:
                t.set_description(query.ticker.upper())
                t.set_postfix(source=query.source)
                t.update()

            urls = self.get_urls(query)
            if not urls:
                logger.debug('No URLs found.')
                continue
                
            urls_found = len(urls)
            logger.debug('urls are {}'.format(json.dumps(urls, indent=4)))
            
            nodes, err = self.build_nodes(query, urls, flags)
            if err:
                logger.error('Error raised in node building phase: {}'.format(err))

            
            if len(nodes):   
                self.update_stocker_stats(urls_found, query.source, len(nodes))              
                self.update_data_file(nodes, query)
                self.update_parsed_urls(urls, query)
            else:
                logger.debug('Node Dictionary is None or has a length of 0, continuing to next iteration.')
              
            utility.sysprint('Fished gathering data for query: {}'.format(query.string))
        
        if gui:
            t.close()
        return nodes
        
    def get_urls(self, query):
        """searches the query in google and returns the resulting urls"""
        url = 'https://www.google.co.in/search?site=&source=hp&q={}&gws_rd=ssl'.format(query.string)
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error getting URL: {} due to err: {}'.format(url, err))
            return None

        soup = BeautifulSoup(resp.content,'html.parser')
        new_urls = []
        for item in soup.find_all('div', attrs={'class' : 'g'}): 
            url = item.a['href'][7:] # offset to get rid of <a href=
            if url:
                if url[0] == '/': url = url[1:]
                if url[:4] != 'http': url = 'http://' + url # attach web protocol, if not there -- default to http

                new_urls.append(url) 
        
        new_urls = [url for url in new_urls if self.is_of_source(url, query.source)]
        logger.debug('found {} links from the query'.format(len(new_urls)))
        return self.remove_dups(new_urls, query.ticker)
    
    def remove_dups(self, urls, ticker):
        """removes already parsed urls from those found by get_urls"""
        logger.debug('removing duplicate links')
        logger.debug('opening file at json path: {}'.format(self.url_file))
        with open(self.url_file, 'r') as f:
            data = json.load(f)
        parsed_urls = data[ticker] if ticker in data.keys() else []
        return [url for url in urls if not (url in parsed_urls)]    

    def build_nodes(self, query, urls, flags):
        """uses the urls to build WebNodes to be written to the csv output"""
        nodes = []
        if len(urls) == 0: 
            logger.debug('Build nodes found no (new) urls to parse (query: {})'.format(query.string))
            return nodes, None
        j = '.'
        company_info, err = self.financeHelper.get_company_info(query.ticker)
        if err:
            company_info = {}
            logger.error('Error getting company information for {}'.format(query.ticker))
        for i, url in enumerate(urls):
            if self.verbose: 
                utility.sysprint('parsing urls for query: {}'.format(query.string) + j*(i % 3))
            
            if self.is_homepage(url, query.source):
                logger.debug('Hit a homepage ({}) ... continuing to next iteration.'.format(url))
                continue
            
            articleParser = ArticleParser(url, query, company_info, **flags)
            node, err = articleParser.generate_web_node()
            if err:
                logger.error('unable to generate node for {} ... continuing to next iteration'.format(url))
                continue
            nodes.append(node)
            
        if self.verbose: 
            utility.sysprint ('built {} Web Nodes'.format(len(nodes)))
        logger.debug('built {} Web Nodes'.format(len(nodes)))

        return nodes, None

    def update_data_file(self, nodes, query):
        """writes the data gathered to a json file"""
        if self.verbose: 
            utility.sysprint('writing {} node(s) to {}'.format(len(nodes), self.data_file))
        logger.debug('writing {} node(s) to {} for query {}'.format(len(nodes), self.data_file, query))
       
        with open(self.data_file, 'r') as f:
            data = json.load(f)
        
        for node in nodes:
            self.qualtricsHandler.submit_node(node)
            key = '+'.join([query.ticker, query.source])
            if key in data.keys():
                sub_nodes = data[key]
                sub_nodes.append(dict(node))
                data[key] = sub_nodes
            else:
                data[key] = [dict(node)]
        
        with open(self.data_file, 'w') as f: 
            json.dump(data, f, indent=4)   

    def update_parsed_urls(self, urls, query):
        """writes parsed links to JSON file to avoid reparsing"""
        if self.verbose: 
            utility.sysprint('writing {} link(s) to {}'.format(len(urls), self.url_file))
        logger.debug('writing {} link(s) to {}'.format(len(urls), self.url_file))
        
        ticker, source = query.ticker.upper(), query.source.lower()
        with open(self.url_file, 'r') as f:
            data = json.load(f)

        # add urls to object
        if ticker in data.keys():
            if source in data[ticker].keys():
                original = data[ticker][source] 
                updated = original + urls 
                data[ticker].update({source : updated})
            else:
                data[ticker].update({source : urls})

        else: 
            sub_obj = {
                ticker: {
                    source: urls
                }
            }
            data.update(sub_obj)

        with open(self.url_file, 'w') as f: 
            json.dump(data, f, indent=4)

    def update_stocker_stats(self, num_urls, source, num_nodes):
        if self.verbose: 
            utility.sysprint('updating stocker stats at {}'.format(self.stats_file))
        logger.debug('updating stocker stats at {}'.format(self.stats_file))
        
        with open(self.stats_file, 'r') as f:
            data = json.load(f)

        # add urls to json
        if source in data.keys():
            original = data[source] 

            # error occuring here
            updated = {}
            updated['num_urls'] = original['num_urls'] + num_urls
            updated['num_nodes'] = original['num_nodes'] + num_nodes
            data.update({source : updated})
        else: 
            data.update({ source : {
                            'num_urls': num_urls,
                            'num_nodes': num_nodes
                    }
            })

        #write the updated json
        with open(self.stats_file, 'w') as f: 
            json.dump(data, f, indent=4)
    
    def is_homepage(self, url, source):
        """Checks to see if it is a homepage for the source. A homepage is not an article, but rather an overview of a stock"""
        regex_map = {
            'bloomberg':    r'bloomberg\.com\/quote\/[a-zA-Z]*:[a-zA-Z]*',
            'yahoo':        r'finance\.yahoo\.com\/quote\/(.?)',
            'seekingalpha': r'seekingalpha\.com\/symbol\/[a-zA-Z]*',
            'reuters':      [   r'reuters\.com\/finance/stocks/overview\/[a-zA-Z]*',
                                r'reuters\.com\/finance\/stocks\/company-news\/[a-zA-Z]*',
                                r'reuters\.com\/finance\/stocks\/companyProfile\/[a-zA-Z]*',
                                r'reuters\.com\/finance\/stocks\/analyst\/[a-zA-Z]*',
                                r'reuters\.com\/finance\/stocks\/chart\/[a-zA-Z]*' ],
            'thestreet':    r'thestreet\.com\/quote\/[a-zA-Z]*'
        }
        if source in regex_map.keys():  
            if isinstance(regex_map[source], list):
                for r in regex_map[source]:
                    if bool(re.compile(r).search(url)):
                        return True
                return False
            return bool(re.compile(regex_map[source]).search(url))
        return False

    def is_of_source(self, url, source):
        """Checks to see if the url is from the intended source"""
        candidates = url.split("://")[1].split("/")[0].split('.')
        for c  in candidates:
            if c == source: 
                return True
        return False