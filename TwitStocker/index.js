'use strict';
const unirest = require('unirest');
const bluebird = require('bluebird');
const Twit = require('twit');
const events = require('events');


// inspired from @KeithCollins botomoter twitbot
// https://github.com/keithcollins/node-botometer

const TwitStocker = function(config) {

	var T = new Twit({
		consumer_key: 	 	 config.CONSUMER_KEY,
		consumer_secret: 	 config.CONSUMER_SECRET,
		access_token: 	 	 config.ACCESS_TOKEN,
		access_token_secret: config.ACCESS_TOKEN_SECRET,
		app_only_auth: 		 config.APP_ONLY_AUTH,
		timeout_ms:          config.TIMEOUT_MS

	});

	// make self reference the TwitStocker instance 
	var self = this;

	const call_delay = config.call_delay || 0;
	const logger = config.logger || true;
	const logger_path = config.logger_path;

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
	};


	this.analyzeTweet = function analyzeTweet(screen_name, tweet) {

		if (tweet.id > (this.lastTweet[screen_name] || 0)) {
			self.lastTweet[screen_name] = tweet.id;

			//emit the event that a new tweet was analyzed
			tweet.screen_name = screen_name;
			self.emit('newTweet', screen_name, tweet);

		}
	};

	this.pollSpawner = function pollSpawner(screen_names, interval) {
		setInterval(function() {
			var screen_name
			for (var i=0; i <screen_names.length; i++) {
				screen_name = screen_names[i]
				console.log('beginning to poll worker for ', screen_name)
				self.pollWorker(screen_name)
				console.log('finished polling worker for ', screen_name)
			}
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



		T.get(path, options, function(err, data, response) {
			if (err) {
				log(err);
			}
			else {
				if (data.length) {
					// analyze and store the tweet
					self.analyzeTweet(screen_name, data[0])

					//update last tweet
					self.lastTweet[screen_name] = data[0].id;

				}
			}
		});
	};

}

// set up the event emmiter and start it
TwitStocker.prototype = new events.EventEmitter;
TwitStocker.prototype.start = function(screen_names, interval) {
	this.pollSpawner(screen_names, interval);
};

// make available to import from other modules
module.exports = TwitStocker;

