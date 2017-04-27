#
#	MAIN
#
#
#

from data_collection import price_change as pc, stocker
from sentiment_analysis import fin_dict, ID3


def read_stocks(path):
	'''
	reads a csv file at the given path and returns an array of the first column
	excluding the first entry (ussually the header)
	'''
	import csv
	f = open(path, 'rb')
	stocks = []
	reader = csv.reader(f)
	for row in reader:
	    stocks.append(row[0])
	f.close()
	return stocks[1:]


def gather_data():
	'''
	gets articles from relavent news sources about each stock in both the NYSE and
	NASDAQ. Data is parsed and matched with associated stock price data to teach a neural network
	to find the connection (if one exisits)
	'''
	NYSE_stocks = read_stocks('../static/NYSE_companylist.csv')
	NASDAQ_stocks = read_stocks('../static/NASDAQ_companylist.csv')

	stocks = NYSE_stocks + NASDAQ_stocks #	6337 STOCKS!

	# build query for each stock + each optimized news source



if __name__ == "__main__":
	"""
	1. Call Stocker to build queries and scape the web
	2. Stocker calls price_change to get associated change in price 
	3. run regressions on data / test out different approaches
	"""
	gather_data()
