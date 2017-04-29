import csv
import urllib2, httplib, requests
import numpy as np

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

def get_data(ticker):
	'''
	Takes in a ticker and a date and returns daily prices (per minute) for that given stock on the
	given date
	returns an array of prices and associated times  
	'''
	r = "1d"
	url = "https://chartapi.finance.yahoo.com/instrument/1.0/"+ticker+"/chartdata;type=quote;range="+r+"/csv"
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	try:
		source_code = urllib2.urlopen(req).read()
	except (urllib2.HTTPError, urllib2.URLError) as e:
		print "Bad URL ", e
		return None, None, None, None, None, None 
	split_source = source_code.split('\n')
	headers = split_source[:17] 	#	TEST TO SEE IF THIS IS ALWAYS THE CASE 
	stock_data = split_source[17:]
	if len(stock_data) == 0:
		return None, None, None, None, None, None 
	for line in stock_data:
		dates, closep, highp, lowp, openp, volume = np.loadtxt(stock_data, delimiter=',', unpack=True)
		
	return dates, closep, highp, lowp, openp, volume

def stringify(data):
	if isinstance(data, list):
		return [str(item) for item in data]
	return str(data)	#	if not a list, return a string of the value

def update_stocks():
	import os
	from datetime import datetime

	today = datetime.today().weekday()

	if today > 4:	# ONLY UPDATE IF THE MARKET IS OPEN
		return None 

	NYSE_stocks = read_stocks('/Users/david/Desktop/Stocker_Threading/static/NYSE_companylist.csv')	# 3143 stocks
	print len(NYSE_stocks)
	# NASDAQ_stocks = read_stocks('/Users/david/Desktop/Stocker_Threading/static/NASDAQ_companylist.csv')

	# stocks = NYSE_stocks + NASDAQ_stocks #	6337 STOCKS!

	for stock in NYSE_stocks:
		path = '/Users/david/Desktop/Stocker_Threading/static/stock_history/'+stock+'.csv'
		print "Getting data for: " + stock
		dates, closep, highp, lowp, openp, volume = get_data(stock)
		if dates == None:
			print "No data"
			continue
		print "Values parsed"
		rows = zip(stringify(dates), stringify(closep), stringify(highp), stringify(openp), stringify(volume))
		print "Rows created "
		if not os.path.isfile(path):	#	create a new file
			with open(path, 'wb') as f:
				writer = csv.writer(f)
				writer.writerows(rows)
				print "Success"
		else:							#	file exists, append new values 
			dates, closep, highp, lowp, openp, volume = get_data(stock)
			with open(path, 'a') as f:
				writer = csv.writer(f)
				writer.writerows(rows)
				print "Success"

if __name__ == "__main__":
	update_stocks()