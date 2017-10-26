'use strict';


const unirest = require('unirest');
const bluebird = require('bluebird');
const Twit = require('twit');
const events = require('events');
const fs = require('fs')

const credential_path = '../credentials.txt'
var twitter_api_key;

fs.readFile(credential_path, function(err, data) {
	if (err) throw err;
	twitter_api_key = data;
});


// inspired from @KeithCollins botomoter twitbot
// https://github.com/keithcollins/node-botometer

const twitstocker = function(config) {

	const T = new Twit(config) {
		consumer_key: 	 	 config.consumer_secret,
		consumer_secret: 	 config.consumer_secret,
		access_token: 	 	 config.access_token,
		access_token_secret: config.access_token_secret,
		app_only_auth: 		 config.app_only_auth
	}

	// look into this 
	var self = this;
	this.T = T;

	const call_delay = config.call_delay || 0;
	const logger = config.logger || true;
	const logger_path = config.logger_path;

	var Event = {
		NewTweet : 'NewTweet'
	}

	var eventEmitter = new events.EventEmitter();
	this.newTweet = eventEmitter;
	this.mostRecent = {};


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

	this.pollSpawner = function pollSpawner(account, interval) {
		setInterval(function() {
			self.pollWorker(account)
		}, interval);
	};


	this.pollWorker = function pollWorker(account) {
		const path = 'statuses/user_timeline';

		T.get(path, options, function(err, data, response) {
			if (err) log(err);

			else {
				// analyze and store the tweet

			}

		});

	}



}


module.exports = twitstocker;