# Stocker

# Dependencies

- Python 2.7
- BeautifulSoup4


```python
import datamine
tickers += ["AAPL", "GOOG", "GPRO", "TSLA"]
sources = ['bloomberg', 'seekingalpha', 'reuters'] # Valid sources are : Bloomberg, seekingAlpha, Reuters
csv_path = '../data/examples.csv'
json_path = '../data/links.json'
dm = datamine.Miner(tickers, sources, csv_path, json_path)
dm.mine()
```

# Machine Learning Aspects

_Handling Missing Attributes_
I did not collect data that did not have all of the following:
- ticker
- url 
- date
This is because without this information, I would be unable to find the correlated stock prices and 
the training example would be rendered useless. Due to this methodology, I did not have any examples with missing attributes in my dataset that I used to build my classifers. 


# Code

The purpose of the overall system is to gather data and use it as input to develop a classifier
to model the data. To do this, I defined a Node struct that correlated to a training example for the input 
to the classifier.

```python
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
        self.score = ps.LM().get_score(words)
        self.subjectivity = self.score['Subjectivity']
        self.polarity = self.score['Polarity']
        self.negative = self.score['Negative']
        self.positive = self.score['Positive']
```