"""
Main.py
Author: David Wallach

This function gathers all of the stock tickers and sources to call datamine.py to fill in the 
data.csv file
"""
import re, time, logging, json
import sys
import requests
from bs4 import BeautifulSoup
from stocker import Stocker, SNP_500, NYSE_Top100, NASDAQ_Top100, valid_sources, querify


def gather_data():
    """
    gets articles from relavent news sources about each stock in the S&P500. 
    Data is parsed and matched with associated stock price data to teach a neural network
    to find the connection (if one exisits)
    """
    # tickers = snp_500()
    # sources = valid_sources()
    # nyse, nasdaq = [], []
    # while len(nyse) == 0: nyse = NYSE_Top100()
    # while len(nasdaq) == 0: nasdaq = NASDAQ_Top100()
    stocks_path = '../data/stocks.json'
    with open(stocks_path, 'r') as f:
        data = json.load(f)
    
    nyse100, nasdaq100, snp500 = data['NYSE100'], data['NASDAQ100'], data['SNP500']
    other_stocks = ['AAPL', 'GOOG', 'GPRO', 'TSLA', 'APRN', 'FB', 'NVDA', 'SNAP', 'SPY', 'NFLX', 'AMZN', 'AMD']
    tickers = nyse100 + nasdaq100 + snp500 + other_stocks
    # tickers = ['ua']
    sources = ['seekingalpha', 'bloomberg', 'reuters']
    csv_path = "../data/examples.csv"
    json_path = "../data/links.json"
    dm = Stocker(tickers, sources, csv_path, json_path)
    dm.stock(depth=2)


def init_logger():
    """ init logger """
    logger = logging.getLogger(__name__)
    format_ = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(format=format_, level=logging.CRITICAL)


def main():
    gather_data()
    
if __name__ == "__main__":
    init_logger()
    main()
    
