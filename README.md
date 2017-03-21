# About Stocker
This is a web scraper I built.
Its main purpose is to track financial data and news about companies; however, it can be used to gather the main words and
sentences from any website.

The main file is stocker.py which builds google queries based on company names, news sources and extra key words.
This is a useful application for getting all the relevant information about a company from the internet. From the data.JSON file, you can use that information how you please. 

#Install
Currently working on an npm package. For now clone the repository 
		>> git clone https://github.com/dwallach1/stocker.git
		>> python stocker.py 	#This will do all the data collection for the queries and write the data to
								#a JSON file 

#How to use
In the main function at the bottom of the stocker.py file there are 3 arrays (companies, news_sources, extra_params) that can be used to construct google queries. It then goes to all through the top 8 google results and parses the urls and finds suburls. The order will be company + news_source + extra_param.

		e.g. companies = ["under armour"]
			 news_sources = ["bloomberg, marketwatch"]
			 extra_params = ["news"]
			 
		These inputs will build the following queries:

			"under armour" + "bloomberg" + "news" >> google >> "under armour bloomberg news"
			"under armour" + "marketwatch" + "news" >> google >> "under armour marketwatch news"

The number of queries run is len(tickers) * len(news_sources) * len(extra_params). Make sure that the queries are built in array format and each portion is its own index. By default the max_depth is set to 0, but you can change it to whatever you wish. When max_depth > 0, all the sublinks embedded in the paragraphs of the article are then also parsed. For this to work efficiently, make sure that the company name you search is the actual name of the company. This is because the program does not parse articles where the company name from the query is not found in the HTML. This is to ensure we do not parse and gather irrelavent data. 

What this does is goes through and finds all the paragraphs written on the pages returned from the orginal google queries and thenuses the natural language toolkit to parse each word and sentence. You can then enable the program to create JSON objects that are written to the data.JSON file by changing the boolean variable write_json in the file getPerception.py. 

You can also enable the program to create an array of tuples of each word and their assocaitave count by changing the boolean variable word_counter at the top of the getPerception.py. Then in wordCounter.py, if you set the export_CSV variable to true, these tuples will be written to a csv file. For this to work, you need to make an empty csv file in your directory called word_count.csv. If you wish to change the name, just update the code in the function csv_export of wordCounter.py. 

#Dependencies
I used BeautifulSoup for getting the raw html data from the web requests and effeciently parse the data for the specific information I thought to be pertinent. This program uses the natural language tool kit (nltk) for efficient word and sentence parsing. It uses pysentitment to access its Harvard IV-4 and Loughran and McDonald Financial Sentiment Dictionaries which are used for sentiment analysis of the data gathered from the queries. 
