"""
Main.py
Author: David Wallach

This function gathers all of the stock tickers and sources to call datamine.py to fill in the 
data.csv file
"""
import logging
import urllib2, httplib, requests
import re
from bs4 import BeautifulSoup
import price_change as pc, datamine
from datamine import *
import time
# from sentiment_analysis import fin_dict, ID3

def get_snp500():
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request("http://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=hdr)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page, "lxml")

    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = list()
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) > 0:
            ticker = str(col[0].string.strip())
            tickers.append(ticker)
    return tickers

def gather_data():
    '''
    gets articles from relavent news sources about each stock in the S&P500. 
    Data is parsed and matched with associated stock price data to teach a neural network
    to find the connection (if one exisits)
    '''
    # tickers = get_snp500()
    # tickers += ["AAPL", "GOOG", "GPRO", "TSLA"]
    # sources = ["Bloomberg", "Seekingalpha"]
    # logger.info('Creating %d nodes' % len(tickers))
    
    tickers = ["UA"]
    sources = ["Bloomberg"] # Valid sources are : Bloomberg, seekingAlpha, Reuters
    # sources = ["seekingalpha"]
    csv_path = '../data/examples.csv'
    json_path = '../data/links.json'
    dm = datamine.Miner(tickers, sources, csv_path, json_path)
    dm.build_queries()
    dm.mine()


def init_logger():
    """ init logger """
    logger = logging.getLogger(__name__)
    format_ = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(format=format_, level=logging.DEBUG)


def main():
    gather_data()
    
if __name__ == "__main__":
    init_logger()
    main()
    
