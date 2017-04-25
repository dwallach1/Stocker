#
#	PRICE CHANGE 
#	
#	-	Uses Yahoo Finace API to get stock prices 
#
#
#	Takes in a stock ticker (e.g. AAPL), a date and a time and finds the change from the preceeding 3 minutes and the 
#	ensuing 3 minutes after the given time.
#
#			 Δprice = price(T + 3 min) - price(T - 3 min)
#
#	returns Δprice (as a float)
#
#

