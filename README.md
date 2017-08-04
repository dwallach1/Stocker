# Stocker
A financial data scraper. Stocker generates google queries to get recent articles and parse them for information. 
All that stocker needs is a list of stock tickers and a list of sources (that correlate to domain names). To store the 
information you can provide a csv path and to make sure you do not parse the same urls, you can provide a json path. 
If you do not want one of these (or either), you can call stocker with the flags csv=False or json=False and leave the path
parameters out when initalizing a Stocker instance. 



```python
from stocker import Stocker

tickers = ['AAPL', 'GOOG', 'GPRO', 'TSLA']		# or define your own set of stock tickers
sources = ['bloomberg', 'seekingalpha', 'reuters']  # and define own set of sources
csv_path = '../data/examples.csv'				# path of where to write output (gathered information)
json_path = '../data/links.json' 				# path of where to write output (for skipping duplicates)
stocker = Stocker(tickers, sources, csv_path, json_path)	# initalize stocker
flags = {'date_checker': True, 'classification': True, 'magnitude': True}
stocker.stock(flags=flags)							# start the stocker
```

Stocker creates queries on its own, based on the stock tickers and sources provided, however, you can define your own
queries.

```python
from stocker import querify
# define our own queries
query_strings = ['under armour most recent articles', 'nikes recent stockholders meeting news']
ticker = 'SNAP'
stocker.queries = [querify(ticker, None, string) for string in query_strings]
stocker.stock(query=False, curious=True)

# or if you want to make sure they are from a certain source
source = 'bloomberg'
stocker.queries = [querify(ticker, source, string) for string in query_strings]
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
from stocker import googler

# Googler takes in a string (what you would type in the search bar) and returns a list of urls generated from the query
# if an error occurs, Googler returns None

results = googler('What is there to do in Berkeley?')
```

# Modules
* __stocker.py__ : manages the overall process, telling webparser which links to parse and takes care of writing the data to disk,
generating queries and handling user flags.
* __webparser.py__ : does the dirty work of parsing articles and storing all of the information in a WebNode.
* __finsent.py__ : after using stocker and webparser to generate a csv file of data, finsent can be used to create and a train
a sentiment analysis classifier.

# Dependencies

- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Dryscrape](http://dryscrape.readthedocs.io/en/latest/installation.html)
- [Requests](http://docs.python-requests.org/en/master/)
- [nltk](http://www.nltk.org/)
- [tqdm](https://github.com/tqdm/tqdm)
- [pytz](https://pypi.python.org/pypi/pytz) 


# Function Parameters
**args for Stocker's stock method**
* gui=True : when set to true uses tdqm to show a progress bar as well as the current ticker & source it is parsing
* csv=True : tells stocker if it should write the output to a csv file
* json=True : tells stocker if it should write the newly parsed links to a json file to avoid duplicates
* flags={} : a dictionary of kwargs to be used when parsing articles
	

	**kwargs recognized by Stocker**
	* ticker=None : used to find information associated with the stock ticker
	* min_length=30 : the minimum amount of words each article must have, only enforced if length_checker = True 
	* curious=False : is set to true, stocker won't ensure that the link it is parsing is from the source field of the query
	* industry=False : looks up and store the industry associated with the ticker 
	* sector=False : looks up and store the industry associated with the ticker
	* date_checker=False : forces each article to have a date; if no date and date_checker is set to true, it will return None
	* length_checker=False : forces each article to have a word count of at least min_length


# Storing Query Data
To store all of the information, every time a url is parsed, a new webnode is generated. After all of the urls are parsed
for a given query, the batch of webnodes are written to the csv file and the parsed urls are stored in the json file under
the stocks ticker (uppercase). Along with the WebNode fields, the stock's ticker is included in each row as well as classification. 
The WedNode's attributes are based on a dictionary that is formed from the flags set in the function call. The attributes set
on the WebNode, will be the headers of the csv file. If you try to combine WebNodes with different attributes in one csv file,
the program will throw an error becuase it is all based on dictionary operations. 
The classification is based on the stock price fluctuations of the associated ticker over a given time interval (default 10 minutes). If 
the stock's price increased, the classification is +1, decreased: -1, and neutral: 0. I am using Google's API for the 
stock prices, they only offer free data (at the minute interval) for the most recent 14 weekdays. For this reason, if there was no 
associated stock price change (becasue the article was published before the past 14 weekdays, I assign the classification a value of 
-1000 to indicate 'not found'.

```python
class WebNode(object):
	"""represents an entry in data.csv that will be used to train the sentiment classifier"""
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
      		setattr(self, key, value)

wn = WebNode(**{'url': url, 'date':date, 'article':article})
wn_dict = dict(wn)
```

I made it easy to convert a WebNode into a dictionary by defining an __iter__ method in the class. This allows Stocker to 
easily write WebNodes to a csv file using a dictwriter. 
