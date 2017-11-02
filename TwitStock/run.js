'use strict';

const fs = require('fs')

const credential_path = '../credentials.txt'
var config;

fs.readFile(credential_path, function(err, data) {
	if (err) throw err;
	config = JSON.parse(data);
});


const twitstocker = new TwitStocker(config);

var screen_name = 'TechCrunch';

// var screen_names = ['TechCrunch', 'Bloomberg']

twitstocker.start(screen_name, WAIT_PERIOD);

twitstocker.on(screen_name, function(action, amount) {
	// maybe tweet from account which stock & how much invested 
	twitStocker.tweet('Just ' + action + ' ' + amount + ' in ' + screen_name);

	console.log('Processed a tweet ', tweet);
});
