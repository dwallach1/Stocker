import stocker
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot
import pylab


class WebDataNode:
	"""
	Data accumulated from google search
	"""

	#class members 
	company = None
	source = None
	date = None
	sentences = []
	words = []
	sentiment = 0.0

	#class methods
 	def __init__(self, name):
 		self.name = name 



def getStockData():
	"""
	get the information about each stock ticker. This function will return a list
	of StockDataNodes
	"""
	tickers = [["APPL", "apple"], ["YHOO", "yahoo"], ["UA", "under armour"], ["GPRO", "go pro"]]
	stock_data_nodes = stockDataParser.parse(tickers)
	return stock_data_nodes



def fillJSON():
	"""
	calls stocker.py to get all the information from the queries
	"""
	stocker.call_functions()


def resetJSON():
	"""
	deletes the current data.json file and makes a new one
	"""
	if os.path.isfile('data.json'):
		os.remove('data.json')




def parseJSON():
	"""
	opens the data.json file and gets all the information.
	Returns an array of WebDataNodes
	"""
	web_data_nodes = []

	with open('data.json') as data_file:
		data = json.load(data_file)

	for entry in data:
		new_node = WebDataNode(entry["url"])
		new_node.company = entry["company"]
		new_node.source = entry["source"]
		new_node.date = entry["date"]
		new_node.sentiment = entry["sentiment"]
		# new_node.sentences = []
		# new_node.words = []
		web_data_nodes.append(new_node)

	# for node in web_data_nodes:
	# 	print node.date

	return web_data_nodes

def get_stock_node_date_list(stock_node):
	"""
	returns a list of dates from the stockDataNode
	"""
	dates = []
	for date in stock_node.dates:
		dates.append(date[0:10])

	return dates


def matcher():
	"""
	match StockDataNodes with WebDataNodes that pertain to the same company 
	and store a tuple of the sentiment values and the historic stock data for the same date
	"""
	coordinates = [] #used to plot (sentiment, day_change_values)

	web_data_nodes = parseJSON()
	stock_data_nodes = getStockData()

	for web_node in web_data_nodes:
		curr_date = web_node.date 
		curr_company = web_node.company
		for stock_node in stock_data_nodes:
			date_list = get_stock_node_date_list(stock_node)
			if curr_date[0:10] in date_list:
				index = date_list.index(curr_date[0:10])
				# print curr_date[0:10]
				# print stock_node.dates[index]
				# print stock_node.company.upper() 
				# print curr_company.upper()
				if stock_node.company.upper() == curr_company.upper():
					match = [web_node.sentiment, stock_node.day_change_values[index]]
					print "matching " + str(web_node.sentiment) + " --> " + str(stock_node.day_change_values[index]) + " --> " + web_node.company.upper() + " --> " + web_node.source.upper()
					coordinates.append(match)


	print("\nLength of coordinate is: " + str(len(coordinates)))
	for coordinate in coordinates:
		print coordinate

	return coordinates

def plotter(coordinates):
	"""
	Plot the coordinates (sentiment, day_change_values) generated from the matching function
	"""
	x = []
	y = []
	for c in coordinates:
		x.append(c[0])
		y.append(c[1])


	matplotlib.pyplot.scatter(x,y)
	matplotlib.pyplot.title('sentiment vs. day_change_values')
	matplotlib.pyplot.xlabel("sentiment")
	matplotlib.pyplot.ylabel("day_change_values")

	matplotlib.pyplot.show()




if __name__ == "__main__":
	resetJSON()
	fillJSON()
	coordinates = matcher()
	plotter(coordinates)

