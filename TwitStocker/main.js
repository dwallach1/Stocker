'use strict';
const spawn = require("child_process").spawn;
const TwitStocker = require('./index.js');


const WAIT_PERIOD = 30*1000;	// 30 seconds
var config = require('./config');

var twitstocker = new TwitStocker(config);

console.log("TwitStocker bot initalized")



// var screen_names = ['TechCrunch', 'Bloomberg']

twitstocker.on('newTweet', function(screen_name, tweet) {
	/*
	 * TWITTER TWEET API PARAMETERS (https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets.html)
	 * 
	 */
	console.log('tweet from: ', screen_name, '(', tweet.created_at, ')', ' ---> ', tweet.text);
});


function decompose_tweet(screen_name, tweet) {


	const URL_REGEX =  new RegExp('(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?');
	const NAME_REGEX = new RegExp('([A-Z][a-z]*)[\s-]([A-Z][a-z]*)');
	const threshold = 0.03;


	// create dictionary of mappings from screen_name to sources
	const name_map = {
		'TechCrunch': 'techcrunch'
	};

	const stocker_path = '../src/main.py';
	const company = NAME_REGEX.exec(text);
	const url = URL_REGEX.exec(text);
	const source = name_map[screen_name];
	var score;
	var action;
	var amount;
	var confidence; 

	// sort through possible company names and check which ones have associated stock ticker
	if (!!company) { company.filter(entry => has_ticker(entry)); }
	
	if (!!url && !!company) {

		// trigger python code
		var process = spawn('python',[stocker_path, arg1, arg2]);

		process.stdout.on('data', function (data){
			// Do something with the data returned from python script
			score = data[0];
			confidence = data[0]

			// log the data
			// logger.log()

			if (score > threshold || score < -threshold) {
				action = score > threshold ? 'invested' : 'shorted';
				amount = score * confidence * 1000;

				// maybe tweet from account which stock & how much invested 
				twitStocker.tweet('Just ' + action + ' ' + amount + ' in ' + company);
			}
		});


	}
	
	console.log('Processed a tweet ', tweet);
};


// start the loop
var screen_names = ['derv_wallach', 'qz', 'business', 'barstoolsports', 'BarstoolBigCat'];
twitstocker.start(screen_names, WAIT_PERIOD);
console.log("TwitStocker bot started ...")

