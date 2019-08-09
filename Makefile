.PHONY: clean

clean:
	echo > data/examples.csv
	echo {} > data/links.json
	echo {} > data/stocker_stats.json

run:
	python3 src/main.py