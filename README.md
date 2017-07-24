# Stocker
This Python package initial's intent was to act as a web scraper for financial articles. It is specialized in parsing 
articles from Bloomberg, SeekingAlpha & Reuters as of writing this. Stocker exports it's findings as a csv file,
allowing people to easily integrate the findings into machine learning models to make sense of the large amount of data.

An example use case is:

```python
import stocker
tickers = ['AAPL', 'GOOG', 'GPRO', 'TSLA']		# array of stock tickers (strings)
sources = ['bloomberg', 'seekingalpha', 'reuters'] 	# specalized sources are : Bloomberg, seekingAlpha, Reuters
csv_path = '../data/examples.csv'				# path of where to write output (gathered information)
json_path = '../data/links.json' 				# path of where to write output (for skipping duplicates)
stocker = Stocker(tickers, sources, csv_path, json_path)	# initalize stocker
stocker.stock()							# start the stocker
```

This project is a personal research project. My goals can be split up into stages:

*__Stage 1__ : explore the correlation between simple financial sentiment analysis and stock price
*__Stage 2__ : build a neural network given stock prices and articles and see if it can form its own financial dictionary
			  by placing weights on different words and such
*__Stage 3__ : if stages 1 & 2 offer anything promising, combine them and see how it performs as an investing strategy


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


# Code

The purpose of the overall system is to gather data and use it as input to develop a model
to classify new, incoming data. To do this, I defined a Node struct that correlated to a training example for the input 
to the classifier. From here, I used [Quantopian](https://www.quantopian.com) to read the csv file, and get the
correlated (w/ regards to time) stock price fluctuations to classify the training data. Following this, I backtested the trading logic, and with a few smoothing methods, I was able to get:
		Return on Investment: 	x%,
		Sharpe Ratio:			x,
		Alpha:					x,
		Beta:					x, 


```python
import pysentiment as py
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
        self.score = ps.LM().get_score(words)			# dict 
        self.subjectivity = self.score['Subjectivity']	# float
        self.polarity = self.score['Polarity']			# float
        self.negative = self.score['Negative']			# float
        self.positive = self.score['Positive']			# float 
```