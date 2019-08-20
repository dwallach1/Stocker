import logging, logging.handlers
import random

from CrawlerService import Stocker
from FinanceService import FinanceHelper
from RequestService import RequestHandler
import UtilityService as utility
from ArticleService import ArticleParser

def gather_data():
    """call financial web scraping API with user defined parameters"""
    
    # rh = RequestHandler()
    # print (rh.generate_proxies())

    financeHelper = FinanceHelper()
    # stock_movers = financeHelper.get_stock_movers()
    # print (stock_movers[:10])
    # print (financeHelper.get_name_from_ticker('AAPL'))
    # print ('sector industry of SAP is: {}'.format(financeHelper.get_company_info('AAPL')))

    nasdaq100 = financeHelper.get_nasdaq_top_100()
    snp500 = financeHelper.get_snp_500()
    nyse = financeHelper.get_nyse()
    stocks = ['SAP', 'AAPL', 'GOOG', 'GPRO', 'TSLA', 'APRN', 'FB', 'NVDA', 'SNAP', 'SPY', 'NFLX', 'AMZN', 'AMD']
    markets = nyse + snp500 + nasdaq100
    random.shuffle(markets)
    random.shuffle(stocks)
    tickers = stocks + markets

    sources = utility.get_valid_sources() 
    
    worker = Stocker(tickers, sources, configpath='credentials.json')

    flags = {
                'date_checker': False, 
                'depth': 1, 
                'validate_url': False, 
                'length_check': True,
                'min_length': 100,            
    }
    worker.stock(flags=flags)
    print ('\n\nFinished Process Successfully.')
   
    # url = 'https://www.investopedia.com/7-tech-companies-that-may-get-bought-next-in-tech-m-and-a-spree-4690575'
    # url = 'https://www.wsj.com/articles/sap-ceo-touts-growth-in-cloud-business-11563426900'
    # query = utility.querify('SAP', 'wsj', 'news')
    # ap = ArticleParser(url, query, financeHelper.get_company_info('SAP')[0])
    # x = dict(ap.generate_web_node()[0])
    # for key in x.keys():
    #     print ('{} : {}'.format(key, x[key]))



def init_logger():
    """ init logger """
    logging.basicConfig(filename='output.log',
                        filemode='w',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

def main():
    init_logger()
    gather_data()
    
if __name__ == "__main__":
    main()
    
