
import logging
import re
from bs4 import BeautifulSoup

from RequestService import RequestHandler
import UtilityService as utility
 

logger = logging.getLogger(__name__)

class FinanceHelper(object):
    """group of methods to gather financial data"""

    def __init__(self, verbose=True):
        self.requestHandler = RequestHandler()
        self.verbose = verbose
    
    def get_snp_500(self):
        """returns a list of the S&P500 stock tickers"""
        if self.verbose: 
            utility.sysprint('Loading SNP500')
        
        url = 'http://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving snp 500s, request returned: {}'.format(err))
            return []

        soup = BeautifulSoup(resp.content, 'lxml')
        table = soup.find('table', {'class': 'wikitable sortable'})
        tickers = []
        for row in table.findAll('tr'):
            col = row.findAll('td')
            if len(col) > 0:
                ticker = str(col[0].string.strip())
                tickers.append(ticker)
        
        if self.verbose: utility.sysprint('Finished loading SNP500')
        return tickers

    def get_nyse_top_100(self):
        """returns a list of the NYSE top 100 stock tickers"""
        if self.verbose: 
            utility.sysprint('Loading NYSE100')
        
        url = 'http://online.wsj.com/mdc/public/page/2_3021-activnyse-actives.html'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving top nyse 100, request returned: {}'.format(err))
            return []
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        tickers = map(lambda stock: re.findall(r'\(.*?\)', stock.text)[0][1:-1], soup.find_all('td', attrs={'class': 'text'}))
        if self.verbose: utility.sysprint('Finished loading NYSE100')
        return tickers

    def get_nasdaq_top_100(self):
        """returns a list of the NASDAQ top 100 stock tickers"""
        if self.verbose: 
            utility.sysprint('Loading NASDAQ100')
        url = 'http://online.wsj.com/mdc/public/page/2_3021-activnnm-actives.html'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving top nasdaq 100, request returned: {}'.format(err))            
            return []
        soup = BeautifulSoup(resp.content, 'html.parser')
        tickers = map(lambda stock: re.findall(r'\(.*?\)', stock.text)[0][1:-1], soup.find_all('td', attrs={'class': 'text'}))
        if self.verbose: 
            utility.sysprint('Finished loading NASDAQ100')
        return tickers 

    def earnings_watcher(self):
        """ returns a list of tickers of which their earning's reports are scheduled to release today (if weekday)"""
        url = 'https://www.bloomberg.com/markets/earnings-calendar/us'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving earning watcher\'s list, request returned: {}'.format(err))            
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        stocks = map(lambda stock: re.search(r'/.*:',stock['href']).group(0)[1:-1], soup.find_all('a', attrs={'class': 'data-table-row-cell__link'}))
        return stocks
    
    def get_sector_industry(self, ticker):
        """
        looks for the associated sector and industry of the stock ticker
        returns -> two strings (first: industry, second: sector)
        :param ticker: associated stock ticker to look up for the information
        :type ticker: string
        """
        industry, sector = '', ''
        url = 'https://www.google.com/finance?&q='+ticker
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.err('Find sector and/or industry flags checked -- Error finding sector and/or industry')
            return None, None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        container = soup.find_all('a')
        next_ = False
        for a in container:
            if next_: 
                industry = a.text.strip()
                break
            if a.get('id') == 'sector': 
                sector = a.text.strip()
                next_ = True
        return industry, sector

    def get_name_from_ticker(self, ticker):
        """convert the ticker to the associated company name"""
        url = 'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en'.format(ticker.upper())
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error finding name for {}. Request returned: {}.'.format(ticker, err))
            return None

        for data in resp.json()['ResultSet']['Result']:
            if data['symbol'] == ticker:
                logger.debug('Matched ticker {} to name {}'.format(ticker, data['name']))
                return data['name']
        return None