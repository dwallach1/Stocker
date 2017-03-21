# -*- coding: utf-8 -*-
# Written by David Wallach
# Copyright of Stocker.io 2017
# This uses our statistical models to 
# rate articles on which we base our investing decisions

#modules
import re
import json
import string 
import unicodedata
import os.path 
from firebase import firebase
from urllib2 import HTTPError
#natural language libraries 
import nltk
# from nltk.classify import NaiveBayesClassifier
# from nltk.corpus import subjectivity
# from nltk.sentiment import SentimentAnalyzer
# from nltk.sentiment.util import *
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pysentiment as ps


firebase = firebase.FirebaseApplication('https://public-eye-e4928.firebaseio.com/')
#declare general variables 
# word_counter = False
write_json = True

global data_glob
data_glob = []

global urls
urls = []
#declare globals 
global sentences
sentences = []

global words 
words = []

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def parser(html, url, company, source, date, title, max_depth):
	"""
	returns the sublinks embedded in the article and
	calls the tokenerizer and sentence parser methods as well as
	the export_to_JSON function if JSON global variable is set to true
	"""
	# if not check_relevance(html, company):
	# 	return []

	# if date == "NULL" and max_depth == 0: 	#if date is null cannot match against historic stock data
	# 										#if max_depth is 0 no need for sublinks
	# 	print "Date is null and max_depth is 0 so not going to parse data nor gather sublinks\n"
	# 	return []

	pertinent_info = []
	sublinks = []
	total_words = []
	total_sentences = []

	total_score = 0.0
	entries = 0

	# print html
	export_html = ""
	pattern = re.compile(r'<p>.*?</p>') #find only the ptag 
	data = pattern.findall(html)
	pertinent_info = pertinent_info + data
	clean_html = ""
	replace_dict = {'<p>': ' ', '</p>': ' ', 
					'<strong>': '', '</strong>': ' ', 
					'<a>': ' ','</a>': '',
					'<em>': ' ', '</em>': ' ',
					'<span>': ' ', '</span>': ' ',
					'<meta>': ' ', '</meta>': ' ',
					'&amp;apos;': ' '
					} #html tags to remove

	for info in pertinent_info:
		robj = re.compile('|'.join(replace_dict.keys())) 
		clean_html = robj.sub(lambda m: replace_dict[m.group(0)], info) #removing the html tags e.g. <p> and </p>
		sublinks_local = re.findall(r'<a.*?>', clean_html, re.DOTALL) #get all sublinks from inside paragraphs of HTML
		clean_html = re.sub(r'<.*?>', ' ',clean_html) #remove all html tags 

		#get rid of all extraneous chars 
		clean_html = re.sub('[^A-Za-z0-9]+', ' ', clean_html, re.DOTALL)

		for link in sublinks_local:
			sublinks.append(link)

		# if date == "NULL":
		# 	print "date is null -- continue to next iteration"
		# 	continue

		# print "\n\n ----------- \n\n"
		# print clean_html

		export_html += clean_html
		html_ascii = html_to_ascii(clean_html)

		# print "\n\n ----------- \n\n"
		# print html_ascii

		# tokens = tokenize(html_ascii)
		# total_sentences.append(sentence_parser(html_ascii))
		# total_words.append(tokens)
		
		score = get_score_LM(clean_html)["Polarity"]
		# score = get_score_HIV4(clean_html)["Polarity"]
		total_score += score
		entries += 1

	total_score_avg = 0.0
	if (entries > 0) and (total_score != 0):
		total_score_avg = total_score / entries
		print bcolors.OKBLUE + "Score is : " + str(total_score_avg) + bcolors.ENDC
	
	# WRITE DATA TO JSON
	# if date != "NULL":
	sentiment = total_score_avg
	print export_html
		# export_JSON(company, url, source, date, sublinks, total_sentences, total_words, sentiment, title, clean_html)
	export_JSON_web(company, url, source, date, sublinks, total_sentences, total_words, sentiment, title, clean_html)

	return sublinks


def export_JSON_web(company, url, source, date, sublinks, total_sentences, total_words, sentiment, title, article_data):
	global data_glob
	data = {
		"title" : title,
		"company" : company.upper(),
		"source" : source,
		"date" : date,
		"url" : url,
		"sublinks" : sublinks,
		"article_data": article_data,
		# "sentences" : sentences,
		# "words" : words,
		"sentiment": sentiment
	}

	data_glob.append(data)
	urls.append(url)
	# try:
	# 	firebase.put('parsed_data',company.upper())
	# 	firebase.put(company.upper(), data)
	# except HTTPError:
	# 	firebase.post('parsed_data',company.upper())
	# 	firebase.post(company.upper(), data)
	# try:
	# 	firebase.put('URLS', urls)
	# except HTTPError:
	# 	firebase.post('URLS', urls)


def return_JSON_List():
	return data_glob


def export_JSON(company, url, source, date, sublinks, sentences, words, sentiment, title, article_data):
	"""
	export the data accumulated from the query to the data.JSON file 
	"""
	data = {
		"title" : title,
		"company" : company.upper(),
		"source" : source,
		"date" : date,
		"url" : url,
		"sublinks" : sublinks,
		"article_data": article_data,
		# "sentences" : sentences,
		# "words" : words,
		"sentiment": sentiment
	}
	firebase.put('parsed_data',company.upper(), data)

	if write_json:
		if os.path.isfile('data.json'):
			with open('data.json') as feedsjson:
				feeds = json.load(feedsjson)

			# feeds.append(data)
			with open('data.json', mode='w') as f:
				feeds.append(data)
				f.write(json.dumps(feeds, indent=2))
			f.close()
		else:
			file = open('data.json', "w")
			file.write("[\n]")
			file.close()
			with open('data.json') as feedsjson:
				feeds = json.load(feedsjson)

			with open('data.json', mode='w') as f:
				feeds.append(data)
				f.write(json.dumps(feeds, indent=2))
			f.close()

	return data



def check_relevance(html, company):
	"""
	checks if article is relevant to the company the program is currently parsing for
	"""

	company_relevant = False
	company_mentions = html
	company_mentions = re.findall(company, company_mentions, re.I)
	if len(company_mentions) > 0:
		company_relevant = True
	if company_relevant:
		print bcolors.OKGREEN +"Article is relevant results : "  + str(company_relevant) + " For company : " + company.upper() + bcolors.ENDC
	else:
		print bcolors.FAIL +"Article is relevant results "  + str(company_relevant) + " For company : " + company.upper() + bcolors.ENDC
	return company_relevant


def html_to_ascii(html):
	"""
	converts unicode data to ascii and ignores the non ascii values
	"""
	html_ascii = ''.join([i if ord(i) < 128 else ' ' for i in html])
	html_ascii = re.sub(r'[^\x00-\x7F]+',' ', html_ascii)
	html_ascii = html.encode("ascii", "ignore")
	return html_ascii


def tokenize(html_ascii):
	"""
	tokenizes the data and removes stopwords
	"""
	tokens = html_ascii.strip().split()

	stopwords = ["the", "and", "this", "is", "in", "the", "when", "where", "who", "a", "t", "s", "we", "amp", "apos"]
   	tokens_minus_stopwords = [word for word in tokens if word.lower() not in stopwords]

	return tokens


def sentence_parser(html_ascii):
	"""
	parses the sentences out of the html 
	"""
	global sentences
	sentences_local = nltk.tokenize.regexp_tokenize(html_ascii, pattern=r'\.(\s+|$)', gaps=True)
	for sentence in sentences_local:
			sentences.append(sentence)
	return sentences_local


def get_score_LM(html):
	"""
	Uses the Landom Mcdonald dictionary for sentiment analysis
	"""
	lm = ps.LM()
	tokens = lm.tokenize(html)
	score = lm.get_score(tokens)
	return score 


def get_score_HIV4(html):
	"""
	Uses the HIV4 dictionary for sentiment analysis
	"""
	hiv4 = ps.HIV4()
	tokens = hiv4.tokenize(html)
	score = hiv4.get_score(tokens)
	return score
