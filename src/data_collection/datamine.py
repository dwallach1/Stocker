#
#	DATAMINE  
# 	Written by David Wallach
# 
#	
#
#
import urllib2, httplib, requests
from bs4 import BeautifulSoup
from datetime import datetime 
from urlparse import urlparse
import time
import re
from price_change import price_change as pc


class Node:
	def __init__(self, title, date, article):
		self.title = title
		self.date = date 
		self.article = article
	
	price_change = None 
	ticker = None


# 	-----------------
#
#	HELPER FUNCTIONS
#
#	-----------------

def check_url(url):
	'''
	ensure the url begins with http
	'''
	valid_schemes = ['http', 'https']
	if (urlparse(url).scheme) in valid_schemes:
		return 1
	return -1


def find_date(soup):
	'''
	returns the content from the BS4 object if a title tag exists,
	else returns an empty string 
	'''
	title = soup.find("title").contents
	if len(title) > 0:
		return title[0]
	return ""

def _date(date):
	return datetime.strptime(date.contents[0].strip('\n'), "%Y-%m-%dT%H:%M:%SZ")

def _article_timestamp(date):
	return datetime.strptime(date['datetime'].strip('\n'), "%Y-%m-%dT%H:%M:%S.%fZ")


def find_date(soup):
	'''
	takes in a beautiful soup object and finds the date field
	gets the date value and format dates as %Y-%m-%d %H:%M:%S
	returns a datetime object of this date
	'''
	IDs = ['date','article-timestamp']

	for ID in IDs:
		date = soup.find(class_= ID)
		if date != None:
			currID = ID
			break

	if date == None: return None 

	options = {
		'date': _date,
		'article-timestamp': _article_timestamp,
	}

	if currID in options.keys():
		return options[currID](date)
	return None 

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f seconds' % (f.func_name, (time2-time1))
        return ret
    return wrap


#	--------------------------------------	
#	
# 	DATA AGGREGATION AND PARSING FUNCTIONS
#
#	--------------------------------------

def parse_article(html):
	'''
	takes out the html tag and concatenates one the article from the soup 
	variable 
	'''
	
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

		export_html += clean_html 
	
	return export_html


def rss_parser(rss_url):
	'''
	some companies offer RSS feeds to their articles which provide faster and more reliable 
	data -- best case is to use RSS feed instead 
	'''
	req = urllib2.Request('https://seekingalpha.com/api/sa/combined/UA.xml', headers={'User-Agent': 'Mozilla/5.0'})
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page.read(), "xml")
	print soup.findAll('title')


def _scrape_url(url):
	'''
	helper function for scrape_url
	''' 
	if check_url(url) < 0:
		return -1

	#	OPEN PAGE AND GET THE HTML
	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), "html.parser")

	#	PICK APART THE SOUP OBJECT
	domain = urlparse(url).hostname.split('.')[1]
	title = find_date(soup)
	date = find_date(soup)
	# soup = unicode.join(u'\n',map(unicode,soup))

	#	FORMAT RESULT 
	result = parse_article(soup)
	if result < 0:
		return result

	# STORE ALL INFORMATION IN A NODE 
	return Node(title, date, article)		#	if we got here, we have successfully parsed the article 

@timing 
def scrape_url(url):
	'''
	takes in a ticker and a url and returns the article body as a string 
	as well as the associated change in stock price 
	'''
	result = _scrape_url(url)
	options {						#	possible error conditions
		-1: "ERROR -- bad url",	
	}

	if result in options.keys():
		return options[result]		#	there was an error, return it 

	return result 					#	successful, return a Node object 

scrape_url('https://www.bloomberg.com/press-releases/2017-04-13/under-armour-announces-nomination-of-jerri-l-devard-to-board-of-directors')
scrape_url('https://www.bloomberg.com/news/articles/2017-02-10/now-under-armour-has-a-trump-problem-too')
scrape_url('https://www.bloomberg.com/news/articles/2017-01-31/under-armour-admits-it-s-still-not-cool-enough')

