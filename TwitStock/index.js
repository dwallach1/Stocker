'use strict';

const unirest = require('unirest');
const bluebird = require('bluebird');
const Twit = require('twit');
const events = require('events');


const WAIT_PERIOD = 30*1000;	// 30 seconds


// inspired from @KeithCollins botomoter twitbot
// https://github.com/keithcollins/node-botometer

var TwitStocker = function(config) {

	const T = new Twit({
		consumer_key: 	 	 config.consumer_secret,
		consumer_secret: 	 config.consumer_secret,
		access_token: 	 	 config.access_token,
		access_token_secret: config.access_token_secret,
		app_only_auth: 		 config.app_only_auth,
		timeout_ms:          config.timeout_ms

	});

	// make self reference the TwitStocker instance 
	var self = this;

	const call_delay = config.call_delay || 0;
	const logger = config.logger || true;
	const logger_path = config.logger_path;

	var Event = {
		NewTweet : 'NewTweet'
	}

	var eventEmitter = new events.EventEmitter();
	this.newTweet = eventEmitter;
	this.lastTweet = {};


	const log = function(msg) {
		if (logger) {
			if (logger_path) {
				fs.writefile(logger_path, msg, function(err) {
					if (err) console.log(err);

					// otherwise do nothing

				});
			} else{
				console.log(msg);
			}
	}

	this.pollSpawner = function pollSpawner(screen_name, interval) {
		setInterval(function() {
			self.pollWorker(screen_name)
		}, interval);
	};


	this.pollWorker = function pollWorker(screen_name) {
		const path = 'statuses/user_timeline';

		const options = {
			'screen_name': 		screen_name,
			'trim_user':   		'true',
			'exclude_replies': 	'true'
		};

		if (self.lastTweet[screen_name]) {
			options.since_id = self.lastTweet[screen_name];
		}


		this.T.get(path, options, function(err, data, response) {
			if (err) log(err);

			else {
				if (data.length) {
					// analyze and store the tweet
					this.analyzeTweet(screen_name, data[0])

					//update last tweet
					self.lastTweet[screen_name] = tweet.id;

				}
			}
		});
	};

	this.analyzeTweet = function analyzeTweet(screen_name, tweet) {

		if (tweet.id > (this.lastTweet[screen_name] || 0)) {
			self.lastTweet[screen_name] = tweet.id;

			//emit the event that a new tweet was analyzed
			tweet.screen_name = screen_name;
			self.emit(screen_name, tweet, amount, );

			//

		}
	};

	//this.batchStock = function batchStock
}

// set up the event emmiter and start it
TwitStocker.prototype = new events.EventEmitter;
TwitStocker.prototype.start = function(screen_name, interval) {
	this.pollSpawner(screen_name, interval);
}

module.exports = TwitStocker;