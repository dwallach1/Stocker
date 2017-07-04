from __future__ import print_function
"""
Main.py
Author: David Wallach

This function gathers all of the stock tickers and sources to call datamine.py to fill in the 
data.csv file
"""
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


def build_queries(tickers, sources):
	queries = []
	for t in tickers:
		for s in sources:
			q = t + '+' + s + '+' + 'stock+articles'
			queries.append([t, s, q])
	return queries

def gather_data():
	'''
	gets articles from relavent news sources about each stock in the S&P500. 
	Data is parsed and matched with associated stock price data to teach a neural network
	to find the connection (if one exisits)
	'''
	# tickers = get_snp500()
	# tickers += ["AAPL", "GOOG", "GPRO", "TSLA"]
	# sources = ["Bloomberg", "Seekingalpha"]
	# assert (len(tickers) > 500)
	# logger.info('Creating %d nodes' % len(tickers))
	
	tickers = ["AAPL", "UA", "GOOG"]
	sources = ["Bloomberg"]
	queries = build_queries(tickers, sources)
	total = len(queries)
	print ('Creating %d workers' % len(tickers))
	print ('Starting to build and write batches ...')
	for i,q in enumerate(queries):
		print("{:2.2%} Complete".format(float(i) / float(total)), end="\r")
		worker = datamine.Worker(q[0], q[1], q[2])
		worker.set_links()
		worker.build_nodes()
		worker.get_writer('../data/')
		writer = worker.writer 
		writer.write_nodes()
		worker.update_links()
	    

	print("{:2.2%} Complete".format(1), end="\r")
	print ('\nDone.')

	
if __name__ == "__main__":
	gather_data()
	
