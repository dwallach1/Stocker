#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""
Main.py
Author: David Wallach

This function gathers all of the stock tickers and sources to call datamine.py to fill in the 
data.csv file. 
"""
import logging, logging.handlers, json
import requests
from bs4 import BeautifulSoup
from stocker import Stocker, SNP_500, NYSE_Top100, NASDAQ_Top100, valid_sources
import os.path



def gather_data():
    """call financial web scraping API with user defined parameters"""
    stocks_path = '../data/stocks.json'
    with open(stocks_path, 'r') as f:
        data = json.load(f)
    
    nyse100, nasdaq100, snp500 = data['NYSE100'], data['NASDAQ100'], data['SNP500']
    other_stocks = ['AAPL', 'GOOG', 'GPRO', 'TSLA', 'APRN', 'FB', 'NVDA', 'SNAP', 'SPY', 'NFLX', 'AMZN', 'AMD']
    tickers = nyse100 + nasdaq100 + snp500 + other_stocks
    sources = valid_sources()
    tickers = other_stocks
    

    # used for testing 
    stocks = ['AAPL', 'GPRO', 'TSLA']
    stocks = other_stocks
    #tickers = ['APRN', 'FB', 'NVDA', 'SNAP']
    # businessinsider not working
    sources = ['seekingalpha', 'bloomberg', 'reuters', 'investopedia', 'marketwatch', 'yahoofinance'] 
    # 'businessinsider', 'googlefinance'


    csv_path = '../data/examples.csv'
    json_path = '../data/links.json'   
    stats_path = '../data/stocker_stats.json'
    dm = Stocker(tickers, sources, csv_path, json_path, stats_path=stats_path)

    flags = {
                'date_checker': True, 
                'depth': 1, 
                'validate_url': False, 
                'length_check': True,
                'min_length': 100,            

    }
    dm.stock(shuffle=True, flags=flags)


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
    
