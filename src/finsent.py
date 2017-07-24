#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import csv
import nltk
from nltk.corpus import names, stopwords
from nltk.classify import apply_features
from nltk import word_tokenize, sent_tokenize, Text, FreqDist, pos_tag
from nltk.corpus import wordnet as wn


# train_size = 0.7(len(examples))
# examples = []
# train, test = examples[:train_size], examples[train_size:]
# stop_words = stopwords.words('english')

''' 	
Tag key:
ADJ -> adjective
ADP -> adposition
ADV -> adverb  
CONJ -> conjunction
DET -> determiner, article
NOUN -> noun
NUM -> numerical
PRT -> particle
PRON -> pronoun
VERB -> verb
. 	 -> punctuation
X 	-> other
'''

class Example(object):
	def __init__(self, tokens):
		self.tokens = tokens
		self.text = Text(tokens)
		self.sentences = sent_tokenize(self.text)
		self.word_count = len(tokens)
		self.word_types = len(set(tokens))
		self.vocab = sorted(set(tokens))
		self.vocab_refined = sorted(set(w.lower() for w in tokens if w.isAlpha()))
		self.word_freq = FreqDist(tokens)
		self.content = [word for word in tokens if word.lower() not in stop_words]
		self.tags = pos_tag(self.text, tagset='universal')


# wnl = nltk.WordNetLemmatizer()
# [wnl.lemmatize(t) for t in tokens]


def parse_csv(path):
	with open(path) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			tokens = word_tokenize(row['article'].decode('utf-8'))
			text = Text(tokens)
			text.collocations()
			print ('length of tokens are {}'.format(len(tokens)))
			# fdist = FreqDist(tokens)
			# for word in sorted(fdist):
			# 	print('{}->{};'.format(word, fdist[word]))
			print (pos_tag(text, tagset='universal'))
			break

'''WordNet is a semantically-oriented dictionary of English, 
consisting of synonym sets — or synsets — and organized into a network.'''

# print (wn.synsets('invest'))
# print (wn.synset('invest.v.01').lemma_names())
# print (wn.synset('invest.v.01').definition())
# print (wn.lemmas('invest'))

parse_csv('../data/examples.csv')