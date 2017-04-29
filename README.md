# About Stocker
Stocker's purpose is to track financial data and news about companies with the purpose of developing an algorithm to help reduce
the error term associated with predicting stock prices. This project is largely a research project because as I try to develop
a machine learning algorithm to be used for (financial) sentiment analysis, I need to learn more about the correlation of articles and the changes in the associated stock prices. 

	* I added <b>stock_daemon.py</b> as a crontab process (running every weekday after the market closes) to track financial data about each stock listed on the NYSE
	by saving daily stockprices by the minute for each stock and saving it to a local csv file. The data was gathered from 
	the Yahoo Finance API. The purpose of this was to avoid having to pay for a service to gather this data. This data was used 
	solely for the research phase.
	* I then scraped the web using <b>datamine.py</b> to get articles on NYSE equities from credible sources and parsed the article bodies and use the timestamps of the article to get the stock price change from time T and T+5 (where T = publishing time of article). The stock price changes are retrieved from the files created from the crontab
	* I then used this information to:
		1. Run regressions to try and find statistical relavence
		2. Build a neural network that represented a financial dictionary 
		3. Test the accuracy of the dictionary against NLTK sentiment analysis and PySentiment 



# Dependencies
<i>Stocker was developed on Python 2.7</i>
	* BeautifulSoup
	* Tensorflow (for the neural network)

