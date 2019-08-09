import os

import logging, logging.handlers
from CrawlerService import Stocker
from FinanceService import FinanceHelper
import utility

def gather_data():
    """call financial web scraping API with user defined parameters"""
    
    # financeHelper = FinanceHelper()
    # nyse100, nasdaq100, snp500 = financeHelper.get_nyse_top_100(), financeHelper.get_nasdaq_top_100(),financeHelper.get_snp_500()
    # other_stocks = ['AAPL', 'GOOG', 'GPRO', 'TSLA', 'APRN', 'FB', 'NVDA', 'SNAP', 'SPY', 'NFLX', 'AMZN', 'AMD']
    # tickers = nyse100 + nasdaq100 + snp500 + other_stocks
    # sources = utility.valid_sources()
    

    # used for testing 
    stocks = ['SAP']
    # sources = ['seekingalpha', 'bloomberg', 'techcrunch', 'marketwatch'] # 'yahoofinance' 
    sources = ['bloomberg']

    dir_path  = os.path.split(os.path.abspath(__file__))[0] + '/'
    csv_path = dir_path + '../data/examples.csv'
    json_path = dir_path + '../data/links.json'   
    stats_path = dir_path + '../data/stocker_stats.json'
    
    worker = Stocker(stocks, sources, csv_path, json_path, stats_path=stats_path)

    flags = {
                'date_checker': False, 
                'depth': 1, 
                'validate_url': False, 
                'length_check': True,
                'min_length': 100,            

    }
    worker.stock(shuffle=True, flags=flags)
    print ('Finished Process Successfully.')

def init_logger():
    """ init logger """
    logging.basicConfig(filename='../data/output.log',
                        filemode='w',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

def main():
    init_logger()
    gather_data()
    
if __name__ == "__main__":
    main()
    
