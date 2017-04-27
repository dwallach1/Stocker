# Written by David Wallach
# Copyright of Stocker.io 2017
import urllib2, httplib, requests
from bs4 import BeautifulSoup
from datetime import datetime 
from urlparse import urlparse
import time
import re
from price_change import price_change as pc

#	------------------
#
#	CLASS DECLARATIONS
#	
#	------------------

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
	'''
	used to determine where the error stems from
	'''
	ERROR_NOERROR = 0
	ERROR_UNIMP = -1
	ERROR_NONEXISTENT = -2
	ERROR_NEWSYMBOL = -3
	ERROR_NOURLS = -4
	ERROR_BADURL = -5
	ERROR_REPEATURL = -6
	ERROR_BADDOMAIN = -7
	ERROR_BADSTATUS = -8
	ERROR_NOPRICEDATA = -9


#
#
#
# HELPER FUNCTIONS
#
#
#
def check_url(url):
	'''
	ensure the url begins with http
	'''
	valid_schemes = ['http', 'https']
	if (urlparse(url).scheme) in valid_schemes:
		return errorCodes.ERROR_NOERROR
	return errorCodes.ERROR_BADURL


def title_formatter(title_html):
	'''
	used to remove the surrounding html from the article titles
	'''
	title = re.findall(r'>(.*?)<',str(title_html),re.DOTALL)
	try:
		return title[0]
	except IndexError:
		return " "


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

	if currID == 'date':
		return datetime.strptime(date.contents[0].strip('\n'), "%Y-%m-%dT%H:%M:%SZ")
	elif currID == 'article-timestamp':
		return datetime.strptime(date['datetime'].strip('\n'), "%Y-%m-%dT%H:%M:%S.%fZ")
	else:
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


def rss_feed_parser(rss_url):
	'''
	some companies offer RSS feeds to their articles which provide faster and more reliable 
	data -- best case is to use RSS feed instead 
	'''
	req = urllib2.Request('https://seekingalpha.com/api/sa/combined/UA.xml', headers={'User-Agent': 'Mozilla/5.0'})
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page.read(), "xml")
	print soup.findAll('title')


def scrape_url(ticker, url):
	'''
	takes in a ticker and a url and returns the article body as a string 
	as well as the associated change in stock price 
	''' 
	if check_url(url) != errorCodes.ERROR_NOERROR:
		return errorCodes.ERROR_BADURL

	req = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

	#	OPEN PAGE AND GET THE HTML
	page = urllib2.urlopen(req)
	soup = BeautifulSoup(page.read().decode('utf-8', 'ignore'), "html.parser")

	#	PICK APART THE SOUP OBJECT
	domain = urlparse(url).hostname.split('.')[1]
	title = title_formatter(soup.find_all("title"))
	date = find_date(soup)

	#	ONCE WE HAVE THE DATE, LOOK FOR ASSOCIATED STOCK PRICE 
	delta_price = pc.price_change(ticker, date)

	if delta_price is None:
		return errorCodes.ERROR_NOPRICEDATA


	print "title is", title, "date is", date
	soup = unicode.join(u'\n',map(unicode,soup))
	parser_result = parse_article(soup)




scrape_url('https://www.bloomberg.com/press-releases/2017-04-13/under-armour-announces-nomination-of-jerri-l-devard-to-board-of-directors')
scrape_url('https://www.bloomberg.com/news/articles/2017-02-10/now-under-armour-has-a-trump-problem-too')
scrape_url('https://www.bloomberg.com/news/articles/2017-01-31/under-armour-admits-it-s-still-not-cool-enough')

