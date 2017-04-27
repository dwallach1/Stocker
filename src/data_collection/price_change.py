#
#	PRICE CHANGE 
#	
#	-	Uses Yahoo Finace API to get stock prices 
#
#	When Stocker's web scraper (main function) finds an article pertaining to a stock, it triggers get_data() 
#	with the associated time 
#	Takes in a stock ticker (e.g. AAPL), a date and a time and finds the change from the preceeding 5 minutes and the 
#	ensuing 3 minutes after the given time.
#
#			 price_change = price(T + 5 min) - price(T - 5 min)
#
#	returns price_change (as a float)
#

from datetime import datetime 
import urllib2
import numpy as np


debug = False


def date_formatter(time_unix):
	'''
	takes in a timestamp in Unix form
	Format dates as %Y-%m-%d %H:%M:%S
	returns a Date 
	'''
	return datetime.fromtimestamp(int(time_unix))	# if we want to make string --> .strftime('%Y-%m-%d %H:%M:%S')


def get_data(ticker):
	'''
	Takes in a ticker and a date and returns daily prices (per minute) for that given stock on the
	given date
	returns an array of prices and associated times  
	'''
	r = "1d"
	url = "https://chartapi.finance.yahoo.com/instrument/1.0/"+ticker+"/chartdata;type=quote;range="+r+"/csv"
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	source_code = urllib2.urlopen(req).read()
	split_source = source_code.split('\n')
	headers = split_source[:17] #	TEST TO SEE IF THIS IS ALWAYS THE CASE 
	stock_data = split_source[17:]

	for line in stock_data:
		dates, closep, highp, lowp, openp, volume = np.loadtxt(stock_data, delimiter=',', unpack=True)

	dates = [date_formatter(d) for d in dates] # convert dates from unix time to comparable format
	print dates
	return dates, closep, highp, lowp, openp, volume


def find_index(dates, time):
	'''
	Finds the index of the associted stock values for the minute the article pertaining to the stock
	was published
	'''
	i = 0
	for date in dates:
		if date.month == time.month and date.day == time.day and date.year == time.year and date.minute == time.minute:
			return i
	return -1

def price_change(ticker, time):
	'''
	Ticker: e.g. UA or AAPL
	Time: Datetime(%Y-%m-%d %H:%M:%S)
	given stock prices for a day, find the price change in the interval (time T, time T + 5 mins)
	returns a float if properly executed
	returns None if error
	'''
	dates, closep, highp, lowp, openp, volume = get_data(ticker)

	index = find_index(dates, time)

	if index < 0:
		return None

	lower_boud = highp[time] - lowp[time]	# (type: float) e.g. price = 30.53 at T
	upper_boud = highp[time+5] - lowp[time+5]	# (type: float) e.g. price = 31.25 at T+5 
	return upper_boud - lower_boud 				# price_change (type: float)

#
#
#	PRICE CHANGE TESTS
#

def date_formatter_test():
	date = date_formatter(1493127038).strftime('%Y-%m-%d %H:%M:%S')
	assert date == "2017-04-25 08:30:38", "date_formatter_test failed"
	# if we got here, we passed the test 
	print "date_formatter_test passed"

if debug:
	date_formatter_test()
