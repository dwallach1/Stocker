# Stocker

> Tesla's stock jumped 2.5% after Tencent said it amassed a 5% stake in the electric car maker. Ocwen jumped 12% premarket after disclosing it reached a deal with New York regulators that will end third-party monitoring of its business within the next three weeks. In addition, restrictions on buying mortgage-servicing rights may get eased.
Cara Therapeutics's shares surged 16% premarket, after the biotech company reported positive results in a trial of a treatment for uremic pruritus.


This project, Stocker, is at its core a financial data scraper. The Python package is itended to generate google queries to get recent articles and parse them for information. 
All that stocker needs is a list of stock tickers and a list of sources (that correlate to domain names).

Due to the closing of Google's and Yahoo's free daily stock price APIs, I decided to create a Twitter bot [StockerBot](https://github.com/dwallach1/StockerBot) that uses the Twitter platform to generate information pertaining to stocks on the user's watchlist. 



Recently, I moved away from the original implementation in the current version because the code was not modularized and the intention of the project ran into roadblocks due to lack of access to historical financial data to build a usable financial sentiment classifier. Furthermore, the open-source ones I found online tended to perform far too poorly to provide any insights. 

I have thus moved the direction of this project to be more of a brand tracker which I go more into depth [here](#V2.0). 

If you want to use the older version, you can still do so by following the directions [here](#V1.0).


## V2.0



## V1.0

Once you clone this repo, you will need to checkout the proper branch

```
git checkout origin v1.0
```


### Example Usage 

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
tested to work for. The current list of verified and tested sources are:

* [Barrons](http://www.barrons.com)
* [Benzinga](https://www.benzinga.com)
* [Bloomberg](https://www.bloomberg.com)
* [BusinessInsider](http://www.businessinsider.com)
* [Investing](https://www.investing.com)
* [Investopedia](http://www.investopedia.com)
* [Investorplace](http://investorplace.com)
* [Zacks](https://www.zacks.com)
* [MarketWatch](http://www.marketwatch.com)
* [MotleyFool](http://motleyfool.com)
* [MSN](http://www.msn.com/en-us/money)
* [Reuters](http://www.reuters.com)
* [SeekingAlpha](http://seekingalpha.com)
* [TheStreet](https://www.thestreet.com)
* [YahooFinance](https://finance.yahoo.com)
* [WSJ](https://www.wsj.com/europe)



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
	

	**kwargs recognized by the Webparser**
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
