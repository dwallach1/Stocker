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

# majority of this code is from : http://bbengfort.github.io/tutorials/2016/05/19/text-classification-nltk-sckit-learn.html
# author : @bbengfort
import os
import time
import string
import pickle

from operator import itemgetter

from nltk.corpus import stopwords as sw
from nltk.corpus import wordnet as wn
from nltk import wordpunct_tokenize
from nltk import WordNetLemmatizer
from nltk import sent_tokenize
from nltk import pos_tag

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import SGDClassifier
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import classification_report as clsr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cross_validation import train_test_split as tts


def timeit(func):
    """
    Simple timing decorator
    """
    def wrapper(*args, **kwargs):
        start  = time.time()
        result = func(*args, **kwargs)
        delta  = time.time() - start
        return result, delta
    return wrapper


def identity(arg):
    """
    Simple identity function works as a passthrough.
    """
    return arg


class NLTKPreprocessor(BaseEstimator, TransformerMixin):
    """
    Transforms input data by using NLTK tokenization, lemmatization, and
    other normalization and filtering techniques.
    """

    def __init__(self, lower=True, strip=True):
        """
        Instantiates the preprocessor, which make load corpora, models, or do
        other time-intenstive NLTK data loading.
        """
        self.lower      = lower
        self.strip      = strip
        self.stopwords  = set(sw.words('english'))
        self.punct      = set(string.punctuation)
        self.lemmatizer = WordNetLemmatizer()

    def fit(self, X, y=None):
        """
        Fit simply returns self, no other information is needed.
        """
        return self

    def inverse_transform(self, X):
        """
        No inverse transformation
        """
        return X

    def transform(self, X):
        """
        Actually runs the preprocessing on each document.
        """
        return [
            list(self.tokenize(doc)) for doc in X
        ]

    def tokenize(self, document):
        """
        Returns a normalized, lemmatized list of tokens from a document by
        applying segmentation (breaking into sentences), then word/punctuation
        tokenization, and finally part of speech tagging. It uses the part of
        speech tags to look up the lemma in WordNet, and returns the lowercase
        version of all the words, removing stopwords and punctuation.
        """
        # Break the document into sentences
        for sent in sent_tokenize(document):
            # Break the sentence into part of speech tagged tokens
            for token, tag in pos_tag(wordpunct_tokenize(sent)):
                # Apply preprocessing to the token
                token = token.lower() if self.lower else token
                token = token.strip() if self.strip else token
                token = token.strip('_') if self.strip else token
                token = token.strip('*') if self.strip else token

                # If punctuation or stopword, ignore token and continue
                if token in self.stopwords or all(char in self.punct for char in token):
                    continue

                # Lemmatize the token and yield
                lemma = self.lemmatize(token, tag)
                yield lemma

    def lemmatize(self, token, tag):
        """
        Converts the Penn Treebank tag to a WordNet POS tag, then uses that
        tag to perform much more accurate WordNet lemmatization.
        """
        tag = {
            'N': wn.NOUN,
            'V': wn.VERB,
            'R': wn.ADV,
            'J': wn.ADJ
        }.get(tag[0], wn.NOUN)

        return self.lemmatizer.lemmatize(token, tag)



@timeit
def build_and_evaluate(X, y, classifier=SGDClassifier, outpath=None, verbose=True):
    """
    Builds a classifer for the given list of documents and targets in two
    stages: the first does a train/test split and prints a classifier report,
    the second rebuilds the model on the entire corpus and returns it for
    operationalization.
    X: a list or iterable of raw strings, each representing a document.
    y: a list or iterable of labels, which will be label encoded.
    Can specify the classifier to build with: if a class is specified then
    this will build the model with the Scikit-Learn defaults, if an instance
    is given, then it will be used directly in the build pipeline.
    If outpath is given, this function will write the model as a pickle.
    If verbose, this function will print out information to the command line.
    """

    @timeit
    def build(classifier, X, y=None):
        """
        Inner build function that builds a single model.
        """
        if isinstance(classifier, type):
            classifier = classifier()

        model = Pipeline([
            ('preprocessor', NLTKPreprocessor()),
            ('vectorizer', TfidfVectorizer(tokenizer=identity, preprocessor=None, lowercase=False)),
            ('classifier', classifier),
        ])

        model.fit(X, y)
        return model

    # Label encode the targets
    labels = LabelEncoder()
    y = labels.fit_transform(y)

    # Begin evaluation
    if verbose: print("Building for evaluation")
    X_train, X_test, y_train, y_test = tts(X, y, test_size=0.2)
    model, secs = build(classifier, X_train, y_train)

    if verbose: print("Evaluation model fit in {:0.3f} seconds".format(secs))
    if verbose: print("Classification Report:\n")

    y_pred = model.predict(X_test)
    print(clsr(y_test, y_pred, target_names=labels.classes_))

    if verbose: print("Building complete model and saving ...")
    model, secs = build(classifier, X, y)
    model.labels_ = labels

    if verbose: print("Complete model fit in {:0.3f} seconds".format(secs))

    if outpath:
        with open(outpath, 'wb') as f:
            pickle.dump(model, f)

        print("Model written out to {}".format(outpath))

    return model


def show_most_informative_features(model, text=None, n=20):
    """
    Accepts a Pipeline with a classifer and a TfidfVectorizer and computes
    the n most informative features of the model. If text is given, then will
    compute the most informative features for classifying that text.
    Note that this function will only work on linear models with coefs_
    """
    # Extract the vectorizer and the classifier from the pipeline
    vectorizer = model.named_steps['vectorizer']
    classifier = model.named_steps['classifier']

    # Check to make sure that we can perform this computation
    if not hasattr(classifier, 'coef_'):
        raise TypeError(
            "Cannot compute most informative features on {} model.".format(
                classifier.__class__.__name__
            )
        )

    if text is not None:
        # Compute the coefficients for the text
        tvec = model.transform([text]).toarray()
    else:
        # Otherwise simply use the coefficients
        tvec = classifier.coef_

    # Zip the feature names with the coefs and sort
    coefs = sorted(
        zip(tvec[0], vectorizer.get_feature_names()),
        key=itemgetter(0), reverse=True
    )

    topn  = zip(coefs[:n], coefs[:-(n+1):-1])

    # Create the output string to return
    output = []

    # If text, add the predicted value to the output.
    if text is not None:
        output.append("\"{}\"".format(text))
        output.append("Classified as: {}".format(model.predict([text])))
        output.append("")

    # Create two columns with most negative and most positive features.
    for (cp, fnp), (cn, fnn) in topn:
        output.append(
            "{:0.4f}{: >15}    {:0.4f}{: >15}".format(cp, fnp, cn, fnn)
        )

    return "\n".join(output)


if __name__ == "__main__":
    PATH = "../data/model.pickle"

    if not os.path.exists(PATH):
        # Time to build the model
        # from nltk.corpus import movie_reviews as reviews

        X = [reviews.raw(fileid) for fileid in reviews.fileids()]
        y = [reviews.categories(fileid)[0] for fileid in reviews.fileids()]

        model = build_and_evaluate(X,y, outpath=PATH)

    else:
        with open(PATH, 'rb') as f:
            model = pickle.load(f)

    print(show_most_informative_features(model))





# class Example(object):
# 	def __init__(self, tokens):
# 		# self.tokens = tokens
# 		self.content = [word for word in tokens if word.lower() not in stop_words]
# 		self.text = Text(tokens)
# 		self.sentences = sent_tokenize(self.text)
# 		self.sentences_tag = [pos_tag(sent) for sent in self.sentences]
# 		self.word_count = len(self.content)
# 		self.word_types = len(set(self.content))
# 		self.vocab = sorted(set(self.content))
# 		self.vocab_refined = sorted(set(w.lower() for w in self.content if w.isAlpha()))
# 		self.word_freq = FreqDist(self.content)
# 		self.tags = pos_tag(self.text, tagset='universal')

# def parse_csv(path):
# 	with open(path) as csvfile:
# 		reader = csv.DictReader(csvfile)
# 		for row in reader:
# 			tokens = word_tokenize(row['article'].decode('utf-8'))
# 			text = Text(tokens)
# 			# text.collocations()
# 			# print ('length of tokens are {}'.format(len(tokens)))
# 			# fdist = FreqDist(tokens)
# 			# for word in sorted(fdist):
# 			# 	print('{}->{};'.format(word, fdist[word]))
# 			tags = pos_tag(text, tagset='universal')
# 			tag_fd = FreqDist(tag for (word, tag) in tags)
# 			# tag_fd.most_common()
# 			tag_fd.tabulate()
# 			break

# '''WordNet is a semantically-oriented dictionary of English, 
# consisting of synonym sets — or synsets — and organized into a network.'''

# # parse_csv('../data/examples.csv')

# def classify():
# 	path = '../data/examples.csv'
# 	data = parse_csv(path)
# 	size = int(0.3*len(data))

# 	grammar = r"""
# 	  NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
# 	  PP: {<IN><NP>}               # Chunk prepositions followed by NP
# 	  VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
# 	  CLAUSE: {<NP><VP>}           # Chunk NP, VP
# 	  """
# 	cp = nltk.RegexpParser(grammar)
# 	cp.parse()


# 	train_set, test_set = [size:], [:size]
# 	classifer = nltk.NaiveBayesClassifier.train(train_set)
# 	acc = nltk.classify.accuracy(classifier, test_set)
# 	print ('accuracy is {4.2f}%'.format(acc))
# 	classifier.show_most_informative_features(5)	
