"""
MAIN
Author: David Wallach
"""


from data_collection import price_change as pc, datamine
from sentiment_analysis import fin_dict, ID3
import urllib2, httplib, requests
from bs4 import BeautifulSoup
import re
import csv


class Query:
	def __init__(self, ticker, source, company):
		self.ticker = ticker
		self.source = source 
		self.company = company

	

def read_stocks(path):
	'''
	reads a csv file at the given path and returns an array of the first column
	excluding the first entry (ussually the header)
	'''
	f = open(path, 'rb')
	stocks = []
	reader = csv.reader(f)
	for row in reader:
	    stocks.append(row[0])
	f.close()
	return stocks[1:]

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
	stocks = get_snp500()
	# stocks = stocks[]
	stocks = ["AAPL", "GOOG", "GPRO", "TSLA"]
	optimized_sources = ["Bloomberg", "Seekingalpha"]
	queries = list()

	for stock in stocks:
		for source in optimized_sources:
			queries.append(Query(ticker=stock, source=source, company=datamine.get_name(stock)))

	urls = datamine.get_urls(queries)

	# build query for each stock + each optimized news source
	# queries = datamine.build_queries(stocks, optimized_sources)
	# urls = [get(url) for url in queries]



if __name__ == "__main__":
	"""
	1. Call Stocker to build queries and scape the web
	2. Stocker calls price_change to get associated change in price 
	3. run regressions on data / test out different approaches
	"""
	gather_data()
	# _parse_rss(Query(ticker="UA", source="Bloomberg", company=datamine.cname_formatter(datamine.get_name("UA"))))
	#_parse_google(Query(ticker="UA", source="Bloomberg", company=datamine.cname_formatter(datamine.get_name("UA"))))
	