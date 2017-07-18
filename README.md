# Datamine
This Python package initial's intent was to act as a web scraper for financial articles. It is specialized in parsing 
articles from Bloomberg, SeekingAlpha & Reuters as of writing this. Datamine exports it's findings as a csv file,
allowing people to easily integrate the findings into machine learning models to make sense of the large amount of data.

An example use case is:

```python
import Datamine
tickers = ['AAPL', 'GOOG', 'GPRO', 'TSLA']		# array of stock tickers (strings)
sources = ['bloomberg', 'seekingalpha', 'reuters'] 	# specalized sources are : Bloomberg, seekingAlpha, Reuters
csv_path = '../data/examples.csv'		# path of where to write output (gathered information)
json_path = '../data/links.json' 	# path of where to write output (for skipping duplicates)
dm = datamine.Miner(tickers, sources, csv_path, json_path)	# initalize miner
dm.mine()			# start the miner
```

# Dependencies

- Python 2.7
- BeautifulSoup4




# Code

The purpose of the overall system is to gather data and use it as input to develop a classifier
to model the data. To do this, I defined a Node struct that correlated to a training example for the input 
to the classifier.

```python
import pysentiment as py
class WebNode(object):
    """represents an entry in data.csv that will be used to train our neural network"""
    def __init__(self, url, pubdate, article, words, sentences, industry='', sector=''):
        self.url = url              # string
        self.pubdate = pubdate      # datetime
        self.article = article      # article
        self.words = words          # list
        self.sentences = sentences  # list
        self.industry = industry    # string
        self.sector = sector        # string
        self.score = ps.LM().get_score(words)	# dict 
        self.subjectivity = self.score['Subjectivity']	# float
        self.polarity = self.score['Polarity']	# float
        self.negative = self.score['Negative']	# float
        self.positive = self.score['Positive']	# float 
```