
import requests
import json
import time
import os


def get_name(ticker):
    """convert the ticker to the associated company name"""
    url = 'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en'.format(ticker.upper())
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4'}
    req = requests.get(url, headers=headers)
    if req.status_code == 503:
    	logger.warn('Request code of 503')
    	time.sleep(30)
    	req = requests.get(url, headers=headers)
    	print('needed to wait')

    req = req.json()
    for data in req['ResultSet']['Result']:
    	if data['symbol'] == ticker:
    		return data['name']




dir_path, file_path = os.path.split(os.path.abspath(__file__))

stocks_path = dir_path + '/data/stocks.json'
with open(stocks_path, 'r') as f:
    data = json.load(f)


nyse100, nasdaq100, snp500 = data['NYSE100'], data['NASDAQ100'], data['SNP500']

stocks = nasdaq100 + nyse100 + snp500

csv = open('stocks.csv', 'w')
headers = 'ticker, name\n'
csv.write(headers)
for stock in stocks:
	name = get_name(stock)
	if name and stock:
		line = stock + ',' + name + '\n'
		csv.write(line)
		print ('wrote line')
	else:
		print ('did not write line')
	time.sleep(20)

csv.close()