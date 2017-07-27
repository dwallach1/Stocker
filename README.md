# Stocker
A financial data scraper. Stocker generates google queries to get recent articles and parse them for information. 
All that stocker needs is a list of stock tickers and a list of sources (that correlate to domain names). To store the 
information you can provide a csv path and to make sure you do not parse the same urls, you can provide a json path. 
If you do not want one of these (or either), you can call stocker with the flags csv=False or json=False. 



```python
from stocker import Stocker

tickers = ['AAPL', 'GOOG', 'GPRO', 'TSLA']		# or define your own set of stock tickers
sources = ['bloomberg', 'seekingalpha', 'reuters'] # and define own set of sources
csv_path = '../data/examples.csv'				# path of where to write output (gathered information)
json_path = '../data/links.json' 				# path of where to write output (for skipping duplicates)
stocker = Stocker(tickers, sources, csv_path, json_path)	# initalize stocker
stocker.stock()							# start the stocker
```

Stocker creates queries on its own, based on the stock tickers and sources provided, however, you can define your own
queries by doing the following.

```python
from stocker import querify
# define our own queries
query_strings = ['under armour most recent articles', 'nikes recent stockholders meeting news']
stocker.queries = map(lambda q: querify(q), query_strings)
stocker.stock(query=False)
```
This package also has built in functions for getting popular stocks as well as a list of the sources that Stocker has been 
tested to work for.

```python
from stocker import SNP_500, NYSE_Top100, NASDAQ_Top100, valid_sources

# get stock tickers
nyse, nasdaq = [], [] 
while len(nyse) == 0: nyse = NYSE_Top100()	# need to poll, because sometime site retuns None
while len(nasdaq) == 0: nasdaq = NASDAQ_Top100()
snp500 = SNP_500()

tickers = nyse + nasdaq + snp500 # list of 700 stock tickers
sources = valid_sources() # use all specialized sources
```

If you want to use stocker as just a means to query google and get a list of results, you can do so.

```python
from stocker import Googler

# Googler takes in a string (what you would type in the search bar) and returns a list of urls generated from the query
# if an error occurs, Googler returns None

results = Googler('What is there to do in Berkeley?')
```

# Modules
* stocker.py
* finsent.py
* webparser.py

# Dependencies

- [Python 2.7](https://www.python.org/download/releases/2.7/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests](http://docs.python-requests.org/en/master/)
- [nltk](http://www.nltk.org/)
- [tqdm](https://github.com/tqdm/tqdm)
- [pytz](https://pypi.python.org/pypi/pytz) 


# Flags
* gui=True
* csv=True
* json=True
* curious=False
* ticker=None
* date_checker=True
* length_checker=False
* min_length=30
* crawl_page=False


# Storing Query Data
To store all of the information, every time a url is parsed, a new webnode is generated. After all of the urls are parsed
for a given query, the batch of webnodes are written to the csv file and the parsed urls are stored in the json file under
the stocks ticker (uppercase). Along with the WebNode fields, the stock's ticker is included in each row as well as classification.
The classification is based on the stock price fluctuations of the associated ticker over a given time interval (default 10 minutes). If 
the stock's price increased, the classification is +1, decreased: -1, and neutral: 0. I am using Google's API for the 
stock prices, they only offer free data (at the minute interval) for the most recent 14 weekdays. For this reason, if there was no 
associated stock price change (becasue the article was published before the past 14 weekdays, I assign the classification a value of 
-1000 to indicate 'not found'.

```python
class WebNode(object):
    """represents an entry in data.csv that will be used to train our neural network"""
    def __init__(self, url, pubdate, article, words, sentences, industry='', sector=''):
        self.url = url              					# string
        self.pubdate = pubdate      					# datetime
        self.article = article      					# article
        self.words = words          					# list
        self.sentences = sentences  					# list
        self.industry = industry    					# string
        self.sector = sector       					    # string
```

