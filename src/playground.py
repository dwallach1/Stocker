# hdr = sorted(['ticker','sector','industry','article','url', 'pubdate', 'sentences','words', 'polarity','subjectivity','negative','positive','priceT0','priceT1','priceT2','priceT3','priceT4','priceT5'])
# from pandas import read_csv
# df = read_csv('../data/examples.csv')
# df.columns = hdr
# df.to_csv('../data/examples_2.csv')

import requests
def get_name(ticker):
    """
    Convert the ticker to the associated company name
    """
    url = 'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query='+ticker+'&region=1&lang=en'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    result = requests.get(url, headers=headers).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == ticker:
            return x['name']


print (get_name('UA'))



"""
notes:

- quant has nothing to do with the company, it uses patterns and numbers to determine
- fundamental data is data concerning the company

# Alpha		: how much of your gains were made irrespective to the market
# Beta		: how much of your gains were made respective to the market ({-0.3, +0.3}, aim for 0)
# Sharpe	: how much risk you took on compared to how much you made (must be > 1 -- 3 is great)
 

# moving average : good at detecting trends
# Max-dropdown : highest high to the lowest subsequent fall (cycle based not full history)

- price to book ratio (pb): how much are all tangible assets vs price of the stock
- price to equity ratio (pe): 
"""