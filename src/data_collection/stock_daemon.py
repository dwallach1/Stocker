"""	
STOCK DAEMON
Author: David Wallach

- Python module that uses Wikipedia to get the companies from the S&P500 and the get_data
	function from price_change.py

this program is meant to be run as a crontab process to download stock market 
data (by the minute) for stocks listed in the S&P500 as well as others to local
files

Gathers ~7.7MB of data every run (per ~505 stocks)
for 52 weeks in a year, running 5 days a week --> ~(52*5*7.7) = 2,002MB = 2.02GB 
"""

import csv
from bs4 import BeautifulSoup
import urllib2, httplib, requests
import numpy as np
from price_change import get_data

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


def stringify(data):
	if type(data) is np.ndarray:
		return [str(item) for item in data]
	return str(data)	#	if not a list, return a string of the value


def update_stocks():
	import os
	from datetime import datetime

	today = datetime.today().weekday()
	if today > 4:	# ONLY UPDATE IF THE MARKET IS OPEN
		return None 

	snp500_stocks = get_snp500()
	other_stocks = ["TSLA", "TWTR", "FB"]
	stocks = snp500_stocks + other_stocks

	for stock in stocks:
		path = '/Users/david/Desktop/Stocker_Threading/static/stock_history/'+stock+'.csv'
		print "Getting data for: " + stock 			# step 1
		dates, closep, highp, lowp, openp, volume = get_data(stock)
		if dates is None:
			print "No data"
			continue
		print "Values parsed"						#	step 2
		rows = zip(stringify(dates), stringify(closep), stringify(highp), stringify(openp), stringify(volume))
		print "Rows created "
		if not os.path.isfile(path):	#	create a new file
			with open(path, 'wb') as f:
				writer = csv.writer(f)
				writer.writerows(rows)
				print "New file Success"						#	step 3 (final)
		else:							#	file exists, append new values 
			dates, closep, highp, lowp, openp, volume = get_data(stock)
			with open(path, 'a') as f:
				writer = csv.writer(f)
				writer.writerows(rows)
				print "Append Success"						#	step 3 (final)

if __name__ == "__main__":
	update_stocks()
