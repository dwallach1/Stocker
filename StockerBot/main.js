'use strict';
const fs = require('fs');
const StockerBot = require('./index.js');


const WAIT_PERIOD = 30*1000;	// 30 seconds
var config = require('./config');

var stockerBot = new StockerBot(config);

console.log("StockerBot initalized")


function is_relevant(screen_name, tweet) {
	/*
	 *
	 *	Aims to see if the tweet is pertaining to any one of the
	 *  stocks in the user's watch list -- if so, then save to disk
	 *
	 */
	// const NAME_REGEX = new RegExp('([A-Z][a-z]*)[\s-]([A-Z][a-z]*)');
	// const company = NAME_REGEX.exec(text);
	return true
}

function classify(screen_name, tweet) {
	/*
	 *
	 *  Aims to classify the tweet into one of the following categories:
	 *	
	 *  	0 - competitor
	 *		1 - the company itself
	 *		2 - general industry of the company
	 */
	 return 1
}

stockerBot.on('newTweet', function(screen_name, tweet) {
	/*
	 * TWITTER TWEET API PARAMETERS (https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/intro-to-tweet-json)
	 * 
	 */

	console.log('tweet from: ', screen_name, '(', tweet.created_at, ')', ' ---> ', tweet.text)

	var urls
	if (tweet.entities.urls) {
		urls = tweet.entities.urls.map(url => url.expanded_url)
	} else {
		urls = []
	}
	console.log(urls)

	var relevant = is_relevant(screen_name, tweet)
	var classification = classify(screen_name, tweet)
});


/*
 *  Load stock data to identify if a tweet is pertaning to a user's stock
 *	list
 */

 function get_user_watchlist() {
 	/*
 	 *
 	 *	This function would get a user's watch list, but for testing & developing reasons
 	 *	it will just load NYSE top 100, SNP500, and a list of other stocks that I am 
 	 * 	curious about
 	 *
 	 */

 	 var data = readFileSync('../data/stocks.json')
 	 var general_stocks - JSON.parse(data)

 	 var nyese100 = general_stocks.nyse100
 	 var snp500 = general_stocks.snp500
 	 var others = [('TSLA', 'tesla'), ('AAPL', 'apple'), ('GPRO', 'gopro'), ('UAA', 'under armour')]

 	 // var stocks = nyse100 + snp500 + others
 }

// start the loop
var screen_names = ['MarketWatch', 'business', 'YahooFinance', 'TechCrunch', 'WSJ', 'Forbes', 'FT', 'TheEconomist', 'nytimes', 'Reuters']
stockerBot.start(screen_names, WAIT_PERIOD)
console.log("StockerBot started ...")

