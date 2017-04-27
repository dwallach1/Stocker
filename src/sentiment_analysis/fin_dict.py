#
#	FIN_DICT (FINANCIAL SENTIMENT DICTIONARY)
#
#	This is a neural network built on Google's Tensor Flow
#	fin_dict takes in an array of dictionary types that have attributes about a specific article and a classifier
#	that is the associated change in stock price.
#
#	
#	The data is formatted follows:
#
#		[{article_sentences: "...", article_words:"...", article_title:"", associated_stock_price_change: 0.41}, ... ]
#
#	The associated stock price change is gathered from 
#		
#
#
#	OVERALL PROCESS
#	
# 	1.	Use Tensor Flow to build neural work of financial library
#		assign each word a numeric value in the range [-1.0, 1.0]
# 		that indicates its weight on the overall sentiment 
#	
#	2.	When we parse a new article, tokenize the article into two arrays.
#		One consisting of all the words in an article (besides stopwords) and 
#		the other made up of all the sentences. Therefore, all the words should
#		appear in both lists.
#
#	FORK 
#	
#	3A.	Develop two seperate neural networks: one for sentence structure and a seperate one for words and
#		see which performs better.
#
#	3B. Use words + sentence structure information to build one neural network and see how it compares to 3A
#	
#
#		** From here we will use either 3A or 3B depending on which performed better **
#
#	
#
#	END
#	
#	**	Does this system perform better than Pysentiment & NLTK? Would it just serve to augment them or can it replace them?
#	
#	**	Test for standard error in (financial) sentiment anlaysis
#
#	**	Can the system detect crucial phrases? (merger, aquisition, CEO leaving) -- test on current stocks like Uber crisis
#
#
#	IDEAS
#	
#	**	See how the neural network works with sentences versus words, need to see what words appear around each word? 
#
#	**	Word's sentiment are not independent but rather are determined by sentence structure?
#	
#	**	Once we build a dictionary, what do we do for new (unseen) words? Ignore them? Add to the dictionary?
#

hot_words = ["bullish", ]

# Store each word with its correlated weight 
class word(): 
  def __init__(self, word, value):
        self.word = word
        self.value = value

  def find_weight(word):
  	for word in dictionary:
  		if word == word:
  			return dictionary[word]
  	return 0.0

