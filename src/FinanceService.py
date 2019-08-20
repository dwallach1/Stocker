
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
        
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving snp 500s, request returned: {}'.format(err))
            return []

        soup = BeautifulSoup(resp.content, 'lxml')
        table = soup.find('table', {'id': 'constituents'})
        tickers = []
        for row in table.findAll('tr'):
            col = row.findAll('td')
            if len(col):
                ticker = str(col[0].get_text().strip())
                tickers.append(ticker)
        
        if self.verbose: utility.sysprint('Finished loading SNP500')
        return tickers

    def get_nyse(self):
        """ """ 
        if self.verbose: 
            utility.sysprint('Loading NYSE')
        page = 1    
        tickers = []
        while page < 64: #64
            url = 'https://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=NYSE&page={}'.format(page)
            if self.verbose:
                utility.sysprint('getting url: {}'.format(url))
            resp, err = self.requestHandler.get(url)
            if err: 
                logger.error('Error retrieving page {} when getting NYSE tickers, request returned: {}'.format(page, err))
                return tickers
            page += 1
            soup = BeautifulSoup(resp.content, 'html.parser')
            table = soup.find('table', {'id': 'CompanylistResults'})
            trs = [tr for idx, tr in enumerate(table.find_all('tr')) if idx % 2]
            for t in trs:
                td = t.find_all('td')[1]
                ticker = td.find('a').get_text()
                tickers.append(re.sub('\s+', '', ticker))
        if self.verbose:
            utility.sysprint('Finished loading NYSE')
        return tickers

    # NOT WORKING 
    def get_stock_movers(self):
        """Includes common stocks, ADRs and REITs listed on NYSE, Nasdaq or NYSE American with a prior day close of $2 a share or higher and volume of at least 50,000"""
        if self.verbose: 
            utility.sysprint('Loading stock movers')
        
        url = 'https://www.wsj.com/market-data/stocks/us/movers'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving top nyse 100, request returned: {}'.format(err))
            return []
        
        tickers = []
        soup = BeautifulSoup(resp.content, 'html.parser')
        rows = soup.find_all('td')
        for row in rows:
            a = row.find('a')
            if a:
                ticker = re.findall(r'\(.*\)', a.get_text()).replace('(', '')
                tickers.append(ticker)
        if self.verbose: utility.sysprint('Finished loading stock movers')
        return list(tickers)

    def get_nasdaq_top_100(self):
        """returns a list of the NASDAQ top 100 stock tickers"""
        if self.verbose: 
            utility.sysprint('Loading NASDAQ100')
        url = 'https://www.cnbc.com/nasdaq-100/'
        resp, err = self.requestHandler.get(url)
        if err: 
            logger.error('Error retrieving top nasdaq 100, request returned: {}'.format(err))            
            return []
        soup = BeautifulSoup(resp.content, 'html.parser')
        table = soup.find('table', {'class': 'quoteTable'})
        tds = table.find_all('td')
        a_tags = [td.find('a') for td in tds if td.find('a')]
        tickers = [re.sub('\s+', '', a.get_text()) for a in a_tags]
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
    
    def get_company_info(self, ticker):
        """ """
        ticker = ticker.upper()
        url = 'https://finance.yahoo.com/quote/{}/profile?p={}'.format(ticker, ticker)
        resp, err = self.requestHandler.get(url)
        if err: 
            e = 'Error finding information for {}. Request returned: {}.'.format(ticker, err)
            logger.error(e)
            return None, e
        
        industry, sector = None, None

        soup = BeautifulSoup(resp.text, 'html.parser')
        parent_container = soup.find('div', {'class': 'asset-profile-container'}).find('div').find('div')
        outer_div = parent_container.find_all('p')[1]

        sector      = outer_div.find_all('span')[1].getText()
        industry    = outer_div.find_all('span')[3].getText()
        
        logger.debug('Found industry: {}, sector: {} for {}'.format(industry, sector, ticker))
        return {
            'industry': industry,
            'sector':   sector,
        }, None

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