"""
Main.py
Author: David Wallach

This function gathers all of the stock tickers and sources to call datamine.py to fill in the 
data.csv file
"""
import re, time, logging
import sys
import requests
from bs4 import BeautifulSoup
from stocker import Stocker, snp_500, valid_sources


def gather_data():
    """
    gets articles from relavent news sources about each stock in the S&P500. 
    Data is parsed and matched with associated stock price data to teach a neural network
    to find the connection (if one exisits)
    """
    # tickers = snp_500()
    # sources = valid_sources()
    tickers = ["AAPL", "GOOG", "GPRO", "TSLA"]
    sources = ['seekingalpha', 'bloomberg']
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
    
