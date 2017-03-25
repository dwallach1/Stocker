# Written by David Wallach
# Copyright of Stocker.io 2017
import urllib2
from bs4 import BeautifulSoup
import re
import numpy as np
import getPerception
import httplib
from dateutil.parser import parse as date_parser
import requests
import threading 
import nltk
import pysentiment as ps
from firebase import firebase
import time
import json

#
#
#
# GLOBAL DECLARATIONS
#

tlock = threading.Lock()
firebase = firebase.FirebaseApplication('https://public-eye-e4928.firebaseio.com/')

global total_urls
total_urls = [] #to avoid repeats
global parsed_urls
parsed_urls = []

global webNodesJSON
webNodesJSON = []


global link_num #used for debugging 
link_num = 1
global total_sentiment 
total_sentiment = []
global total_entries 
total_entries = []

debugger = False 

#
#
#
# CLASS DECLARATIONS
#
#
class bcolors:
	""" 
	used to style the output strings printed to the console
	"""
   	HEADER = '\033[95m'
   	OKBLUE = '\033[94m'
   	OKGREEN = '\033[92m'
   	WARNING = '\033[93m'
   	FAIL = '\033[91m'
   	ENDC = '\033[0m'
   	BOLD = '\033[1m'
   	UNDERLINE = '\033[4m'

class errorCodes:
	ERROR_NOERROR = 0
	ERROR_UNIMP = -1
	ERROR_NONEXISTENT = -2
	ERROR_NEWSYMBOL = -3
	ERROR_NOURLS = -4
	ERROR_BADURL = -5
	ERROR_REPEATURL = -6
	ERROR_BADDOMAIN = -7

class WebNode: 

	sentences = []
	words = []
	wordCount = 0
	sentiment = 0.0
	polarity = 0.0
	negative = 0
	positive = 0
	childNodes = []
	article_data =""

	def __init__(self, company, url, source, date="NULL", title="NULL"):
		self.company = company
		self.url = url
		self.source = source
		self.date = date 
		self.title = title

global rando
rando = 0

#
#
#
# DATA AGGREGATION AND PARSING FUNCTIONS
#
#
def build_queries(companies, news_sources, extra_params):
	"""
	takes in an array of companies, news sources and extra parameters and
	builds a list of qeuries
	"""
	queries = []
	for i,company in enumerate(companies):
		for j,sources in enumerate(news_sources):
			for k,params in enumerate(extra_params):
				queries.append([companies[i], news_sources[j], extra_params[k]])

	print("****************************")
	print("QUEREIS (" + str(len(queries)) +") : ")
	print("****************************")

	for i in queries:
		print(bcolors.OKBLUE + i[0] + " " + i[1] + " " + i[2] + bcolors.ENDC)
	return queries

def web_scraper(queries, max_depth):
	"""
	takes in a list of queries and a integer for the depth of sublink traversals.
	It sends the list of queries to google and gets a list of URLs from the google result.
	It then calls get_info to get the necessary data from the URL
	"""
	thread_inputs = []
	i = 0 
	for i in range(0,len(queries)):

		query = queries[i][0] + " " + queries[i][1] + " " + queries[i][2]
		query=query.strip().split()
		query="+".join(query)

		#html request and Beautiful Soup parser 
		html = "https://www.google.co.in/search?site=&source=hp&q="+query+"&gws_rd=ssl"
		req = urllib2.Request(html, headers={'User-Agent': 'Mozilla/5.0'})
		soup = BeautifulSoup(urllib2.urlopen(req).read(),"html.parser")

		#Re to find URLS
		reg=re.compile(".*&sa=")

		#get all web urls from google search result 
		links = []
		# for item in soup.find_all('h3', attrs={'class' : 'r'}):
		for item in soup.find_all(attrs={'class' : 'g'}):
			link = (reg.match(item.a['href'][7:]).group())
			date = re.findall(r'class="st">.*?<',str(item))
			date = re.findall(r'>.*?<',str(date))
			date = re.sub(r'[><]', '', str(date))
			date = date_formatter(date[1:len(date)-1])
		   	link = link[:-4]
		   	url = link.rstrip().replace("u'","")
			url = link.rstrip().replace("'","")
			links.append(url)
		   	node = WebNode(company=queries[i][0], url=[url], source=queries[i][1], date=date)
		   	thread_inputs.append(node)

		if debugger:
			print links

		j = 0
		for j in range(0,3):
			print('**********************************\n')

		print "URLs to parse:"
		print bcolors.BOLD + '--------------------------------------'
		for link in links:
			print link  
		print '--------------------------------------' + bcolors.ENDC		
		i += 1

	threads = []
	for i in range(0, len(thread_inputs)):
	   	t = threading.Thread(target=get_info, args=(thread_inputs[i], 0, max_depth))
	   	threads.append(t)
	   	t.start()

	for i in range(0, len(threads)):
	   	t = threads[i]
	   	t.join()

def get_info(webNode, depth, max_depth):
	"""
	parses the links and gathers all the sublinks as well as calls
	other functions to gather the pertinent data and perform the sentiment analysis
	"""
	global link_num
	global total_urls
	global rando

	links = webNode.url
	source = webNode.source
	company = webNode.company
	date = webNode.date
	traverse_sublinks = False
	print "length of links is " + str(len(links))
	for url in links:
		# if link_num > 5:
		# 	return
		link_num += 1
		if debugger:
			tlock.acquire()
			print bcolors.BOLD + "-------------- ..... NEW LINK || TRYING LINK NUMBER : " + str(link_num) + " ..... ----------------" + bcolors.ENDC
			link_num += 1
			tlock.release()
			
		if check_url(url) != errorCodes.ERROR_NOERROR:
			return errorCodes.ERROR_BADURL

		total_urls.append(url)
		req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

		try:
			#OPEN PAGE AND GET THE HTML
			page = urllib2.urlopen(req)
			soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), "html.parser") 

			#USED FOR PARSING CORRECT INFORMATION
			domain = find_domain(url)

			if source.upper() != domain:
				print bcolors.FAIL + "url from external source -- skipping" + bcolors.ENDC
				return errorCodes.ERROR_BADDOMAIN

			url_type = find_url_type(url)

			#HOMEPAGE == TRUE, SO PARSE EMBEDDED LINKS W/O PARSING HOMEPAGE
			if find_homepage_url(domain) == url_type:
				traverse_sublinks = True
				rando += 1

			#GET THE TITLE FOR DISPLAY PURPOSES
			article_title = soup.find_all("title") 
			article_title = title_formatter(article_title)
			
			#GATHER ALL SUBLINKS IN CASE WE NEED TO TRAVERSE FURTHER 
			sublinks_class = find_sublink_class(source)
			sublinks = soup.find_all(attrs={'class' : sublinks_class})
			sublinks = sublink_parser(sublinks, source)

			#PRINTING TO THE CONSOLE 
			tlock.acquire()
			print "Scraping web for company : " + bcolors.HEADER + company.upper() + bcolors.ENDC
			print "Currently parsing article : " + article_title + "\n" + "From source : "+ source 
			print "URL is : " + url
			print "Date posted : " + str(date)
			print bcolors.OKGREEN + "HTTP Status of Request : " + str(page.getcode()) + "\n" + bcolors.ENDC
			print domain
			print url_type
			print traverse_sublinks
			tlock.release()

			#CONVERT HTML TO STRING FORMAT AND PARSE INFO
			if traverse_sublinks == False:
				soup = unicode.join(u'\n',map(unicode,soup))
				traverse_sublinks = parser(soup, webNode, max_depth)

		except (urllib2.HTTPError, urllib2.URLError) as e:
			try:
				print bcolors.FAIL + "Uh oh there was an HTTP error with opening this url: \n" + str(url)+ "\n" + "Error code " + str(e.code) + "\n" + bcolors.ENDC
				continue
			except AttributeError:
				print bcolors.FAIL + "Uh oh there was an HTTP error with opening this url: \n" + str(url)+ "\n" + bcolors.ENDC
				continue
		except httplib.BadStatusLine:
			print bcolors.FAIL + "\nUh oh we could not recognize the status code returned from the http request\n" + bcolors.ENDC
			continue

		if traverse_sublinks and depth < max_depth:
			threads = []
			for i in range(0, len(sublinks)):
				childNode = WebNode(url=[sublinks[i][0]], company=company, source=sublinks[i][2].upper(), date=date_formatter(sublinks[i][1]))
				t = threading.Thread(target=get_info, args=(childNode, depth+1, max_depth))
				threads.append(t)
				t.start()

			for i in range(0, len(threads)):
			   	t = threads[i]
			   	t.join()

		return errorCodes.ERROR_NOERROR

def parser(html, webNode, max_depth):
	"""
	returns the sublinks embedded in the article and
	calls the tokenerizer and sentence parser methods as well as
	the export_to_JSON function if JSON global variable is set to true
	"""
	global total_sentiment
	global total_entries
	
	parseChildren = False
	export_html = ""

	article_data = []

	pattern = re.compile(r'<p>.*?</p>') #find only the ptag 
	data = pattern.findall(html)
	article_data = article_data + data
	commentSoup = BeautifulSoup(html, "html.parser")
	preTags = commentSoup.findAll('pre')
	try:
		data2 = preTags[0]
		if debugger:
			print data2
		article_data += data2
	except:
		pass	


	clean_html = ""
	replace_dict = {'<p>': ' ', '</p>': ' ', 
					'<strong>': '', '</strong>': ' ', 
					'<a>': ' ','</a>': '',
					'<em>': ' ', '</em>': ' ',
					'<span>': ' ', '</span>': ' ',
					'<meta>': ' ', '</meta>': ' ',
					'&amp;apos;': ' '
					} #html tags to remove

	for data in article_data:
		robj = re.compile('|'.join(replace_dict.keys())) 
		clean_html = robj.sub(lambda m: replace_dict[m.group(0)], data) #removing the html tags e.g. <p> and </p>
		clean_html = re.sub(r'<.*?>', ' ',clean_html) #remove all html tags 
		clean_html = re.sub('[^A-Za-z0-9]+', ' ', clean_html, re.DOTALL) #get rid of all extraneous chars 

		# if date == "NULL":
		# 	print "date is null -- continue to next iteration"
		# 	continue

		export_html += clean_html 
	
	sentiment = get_score_LM(export_html)
	polarity = sentiment["Polarity"]
	subjectivity = sentiment["Subjectivity"]
	negative = sentiment["Negative"]
	positive = sentiment["Positive"]

	if polarity == 0:
		parseChildren = True
	else:
		total_sentiment.append(polarity)
		total_entries.append(1)

	webNode.sentiment = polarity
	webNode.polarity = polarity
	webNode.subjectivity = subjectivity
	webNode.negative = negative
	webNode.positive = positive
	webNode.article_data = export_html

	tlock.acquire()
	print "--------------**********-------------------"
	print bcolors.OKBLUE + "Score is : " + str(sentiment) +  " for url: " + webNode.url[0] + bcolors.ENDC
	print subjectivity
	print negative
	print positive 
	print parseChildren
	print "--------------**********-------------------"
	tlock.release()
	
	export_JSON_web(webNode)
	return parseChildren

def export_JSON_web(webNode):
	global webNodesJSON
	global parsed_urls
	data = {
		"title" : webNode.title,
		"company" : webNode.company.upper(),
		"source" : webNode.source,
		"date" : webNode.date,
		"url" : webNode.url[0],
		"article_data": webNode.article_data,
		"sentiment": webNode.sentiment
	}

	webNodesJSON.append(data)
	parsed_urls.append(webNode.url[0])


#
#
#
# HELPER FUNCTIONS
#
#
#
def check_url(url):
	if(url[0:4] != "http") or url[len(url) - 3:] == "jpg":
		print "\n" + bcolors.FAIL + "URL is :" + url + bcolors.ENDC
		print bcolors.FAIL + "Bad URL continuing to the next one" + bcolors.ENDC + "\n"
		return errorCodes.ERROR_BADURL

	if url in total_urls:
		print "\n" + bcolors.FAIL + "URL is : " + url + bcolors.ENDC
		print bcolors.FAIL + "Already parsed -- skipping to the next one" + bcolors.ENDC + "\n"
		return errorCodes.ERROR_REPEATURL

	return errorCodes.ERROR_NOERROR

def title_formatter(title_html):
	"""
	used to remove the surrounding html from the article titles
	"""
	title = re.findall(r'>(.*?)<',str(title_html),re.DOTALL)
	try:
		return title[0]
	except IndexError:
		return " "

def date_formatter(date):
	"""
	format the date in a uniform way to be able to compare.
	Gets the input date and returns it in MM/DD/YY format (e.g. 2/6/17)
	"""
	try:
		date_formatted = str(date_parser(date))
	except (ValueError, AttributeError, OverflowError) as e:
		print e
		print bcolors.WARNING +  "date set to default 'NULL' value" + bcolors.ENDC
		date_formatted = "NULL"

	if debugger:
		print date
	return date_formatted

def find_domain(url):
	try:
		pattern = re.compile(r'www.*?com')
		domain_full = pattern.findall(url)[0]
		domain = domain_full[4:len(domain_full)-4]
		return domain.upper()
	except:
		print "domain is null"
		print url
		return 'NULL'

def find_url_type(url):
	try:
		pattern = re.compile(r'com/.*?/')
		url_type_full = pattern.findall(url)[0]
		url_type = url_type_full[4:len(url_type_full)-1]
		return url_type.upper()
	except:
		return 'NULL'

def find_sublink_class(source):
	"""
	each of the finance websites company landing pages has different classes for related articles
	this function directs the program to the proper one
	"""
	try:
		return {
		'Bloomberg': 'news-story',
		'BLOOMBERG': 'news-story',
		'SeekingAlpha': 'symbol_article',
		'INVESTOPEDIA': 'by-author'
		}[source]
	except TypeError:
		return 'unknown'

def find_homepage_url(domain):
	"""
	each of the finance websites company landing pages has different classes for related articles
	this function directs the program to the proper one
	"""
	try:
		return {
		'BLOOMBERG': 'QUOTE',
		'SEEKINGALPHA': 'SYMBOL',
		}[domain]
	except:
		return errorCodes.ERROR_NONEXISTENT

def sublink_parser(sublinks, source):
	sublink_info = []
	if source == 'Bloomberg':
		for link in sublinks:
			url = re.findall(r'href=.*?>',str(link))
			url = url[0][6:len(url)-3]
			date = re.findall(r'datetime=.*?>',str(link))
			date = date[0][10:len(date)-3]

			#APPLICABLE IF WE WANT TO ALLOW ALL DOMAINS
			# new_source = re.findall(r'www.*?com', url)
			# new_source = new_source[0][4:len(new_source)-5]
			sublink_info.append([url, date, source])
	if debugger:
		tlock.acquire()
		print sublink_info
		tlock.release()
	return sublink_info

def return_webNodesJSON():

	return webNodesJSON

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

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f seconds' % (f.func_name, (time2-time1))
        return ret
    return wrap

@timing
def get_score_LM(html):
	"""
	Uses the Landom Mcdonald dictionary for sentiment analysis
	"""	
	lm = ps.LM()
	tokens = lm.tokenize(html)
	tlock.acquire()
	print "num tokens is: " + str(len(tokens))
	tlock.release()
	score = lm.get_score(tokens)
	if debugger:
		tlock.acquire()
		print "getting sentiment"
		print tokens
		tlock.release()
	return score 

# def gather_stock_data():
	#http://chart.finance.yahoo.com/table.csv?s=UA&a=2&b=6&c=2012&d=2&e=6&f=2017&g=d&ignore=.csv

def get_symbol(symbol):
	"""
	Convert the ticker to the associated company name
	"""
	url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
	result = requests.get(url).json()
	
	for x in result['ResultSet']['Result']:
		if x['symbol'] == symbol:
			return x['name']

@timing
def load_DB(symbol):
	global parsed_urls 
	path = '/'
	result = firebase.get(path, symbol)
	if result == None:
		val = {'data': 'NULL'}
		# val_json = json.dumps(val)
		result = firebase.put(path, symbol, val_json)
		if result != val:
			rc = errorCodes.ERROR_NEWSYMBOL
			return rc
		path += '/' + symbol + '/' + 'data'
		# snapshot = 'data'
		val = 'NULL'
		# result = firebase.put(path, snapshot, val)
		result = firebase.patch(path, val)
	result = firebase.get(path, 'parsed_urls')
	if result == None:
		return errorCodes.ERROR_NOURLS
	parsed_urls += result
	return errorCodes.ERROR_NOERROR




#
#
#
# MAIN
#
#
@timing
def Main():
	"""
	call the functions to create queries and run web scraper
	"""
	max_depth = 1
	symbol = "AAPL"
	company = get_symbol(symbol)
	news_sources = ["Bloomberg"]
	extra_params = ["news"]
	company = re.sub(r'Inc\.', '', company)
	company = re.sub(r'Corporation', '', company)
	company = [company]

	# markit(symbol)

	# rc = load_DB(symbol)
	# print rc
	queries = build_queries(company, news_sources, extra_params)
	web_scraper(queries, max_depth) 
	# #
	# #
	# # UPDATE DB
	# if rc == errorCodes.ERROR_NOURLS:
	# 	path = '/' + symbol.upper() + '/' + 'parsed_urls'
	# 	total_links = parsed_urls + total_urls
	# 	snapshot = 'parsed_urls'
	# 	# result = firebase.put(path, snapshot, total_links)
	# 	result = firebase.patch(path, total_links)
	# 	print result
	# 	if result != total_links:
	# 		print "Unable to update parsed_urls in firebase"



	if len(total_entries) > 0:
		print sum(total_sentiment)/len(total_entries)
	else:
		print "zero entries"
	print "Total entries w/ sentiment greater than 0: " + str(len(total_entries))
	print rando
	print real_news

if __name__ == "__main__":
	Main()
