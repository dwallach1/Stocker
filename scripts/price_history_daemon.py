"""	
STOCKER DAEMON
Author: David Wallach

- Python module that uses Wikipedia to get the tickers from different stock exchanges and the get_data
	function from price_change.py

this program is meant to be run as a crontab process to download stock market 
data (by the minute) for stocks listed in the S&P500 as well as others to local
files

Gathers ~7.7MB of data every run (per ~505 stocks)
for 52 weeks in a year, running 5 days a week --> ~(52*5*7.7) = 2,002MB = 2.02GB 
"""

import os
from datetime import datetime
import csv
import json
import numpy as np
import requests
import logging, logging.handlers
import time

# globals used to retrieve data
crumble_link = 'https://finance.yahoo.com/quote/{0}/history?p={0}'
crumble_regex = r'CrumbStore":{"crumb":"(.*?)"}'
cookie_regex = r'Set-Cookie: (.*?); '
quote_link = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb={}'


def date_formatter(time_unix):
	from pytz import timezone
	'''
	takes in a timestamp in Unix form
	Format dates as %Y-%m-%d %H:%M:%S
	returns a Date 
	'''
	date_UTC = datetime.fromtimestamp(int(time_unix))	#	dates come in Unix time and converted to local 
	date1, date2 = datetime.now(timezone('US/Eastern')), datetime.now()
	rdelta = date1.hour - date2.hour 					#	convert local time to EST (the timezone the data was recorded in)
	return date_UTC + timedelta(hours=rdelta)			#	via yahoo API
	#	final date varies by seconds on each variation -- changes between 9:30 and 9:31 -- due to fromtimestamp conversion

def get_cookies(ticker):
	link = crumble_link.format(ticker)
	#response = urllib2.urlopen(link)
	r = requests.get(link)
	r_headers = r.headers
	# match = re.search(cookie_regex, str(response.info()))
	match = re.search(cookie_regex, str(r_headers))
	cookie_str = match.group(1)
	text = r.text
	match = re.search(crumble_regex, text)
	crumble_str = match.group(1)
	return crumble_str, cookie_str

def get_data(ticker, day):
	#url = "https://chartapi.finance.yahoo.com/instrument/1.0/"+ticker+"/chartdata;type=quote;range=1d/csv"
	quote_link 
	headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; MotoG3 Build/MPI24.107-55) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.81 Mobile Safari/537.36'}
	req = requests.get(url, headers=headers)

	source_code = req.text
	split_source = source_code.split('\n')
	headers = split_source[:17] #	TEST TO SEE IF THIS IS ALWAYS THE CASE || maybe get the sector and such information?
	stock_data = split_source[17:]

	if len(split_source) < 18:
		return None, None, None, None, None, None

	for line in stock_data:
		dates, closep, highp, lowp, openp, volume = np.loadtxt(stock_data, delimiter=',', unpack=True)

	dates = [date_formatter(d) for d in dates] # convert dates from unix time to comparable format
	return dates, closep, highp, lowp, openp, volume


def stringify(data):
	if type(data) is np.ndarray:
		return [str(item) for item in data]
	return str(data)	#	if not a list, return a string of the value


def update_stocks(day=None, create=False,Path=None):
	
	# if no inputted day, default to today
	if day == None:
		day = datetime.today().weekday()
	
	# only update is the market is open
	if day > 4:	
		return None 

	# read the stock tickers from the JSON file
	stocks_path = '../data/stocks.json'
	with open(stocks_path, 'r') as f:
		data = json.load(f)

	nyse100, nasdaq100, snp500 = data['NYSE100'], data['NASDAQ100'], data['SNP500']
	other_stocks = ['AAPL', 'GOOG', 'GPRO', 'TSLA', 'APRN', 'FB', 'NVDA', 'SNAP', 'SPY', 'NFLX', 'AMZN', 'AMD']
	stocks = nyse100 + nasdaq100 +  snp500 + other_stocks

	# iterate over each stock 
	for stock in stocks:
		# path = os.path.abspath(os.path.join(__file__ ,"../..")) + '/static/stock_history/' +stock+'.csv'
		path = os.path.abspath(__file__ ) + '/stock_history/'+stock+'.csv'
		# path = '/Users/david/Desktop/Stocker_Threading/static/stock_history/'+stock+'.csv'
		
		logger.debug ('Getting data for: ' + stock )			# step 1
		dates, closep, highp, lowp, openp, volume = get_data(stock, day)
		

		if dates is None:
			# no data -- continue to next stock
			logger.warn('No data for stock {}'.format(stock))
			continue
		
		logger.debug ('Values parsed for stock {}'.format(stock))						#	step 2
		rows = zip(stringify(dates), stringify(closep), stringify(highp), stringify(openp), stringify(volume))
		logger.debug ('Rows created for stock {}'.format(stock))
		
		if not os.path.isfile(path):	#	create a new file
			with open(path, 'wb') as f:
				writer = csv.writer(f)
				writer.writerows(rows)
				logger.debug('New file Success for stock {}'.format(stock))	 #	step 3 (final)
		
		# file exists, append new values 
		else:							
			with open(path, 'a') as f:
				writer = csv.writer(f)
				writer.writerows(rows)
				logger.debug('Append Success for stock {}'.format(stock))						

def init_logger():
    """ init logger """
    path = os.path.abspath(__file__ ) + '/daemon_output.log'
    logging.basicConfig(filename=path,
                        filemode='w',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)


if __name__ == '__main__':
	init_logger()
	update_stocks()


