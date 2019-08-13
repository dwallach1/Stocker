.PHONY: clean

clean:
	rm -rf data
	mkdir data
	echo {} > data/data.json
	echo {} > data/urls.json
	echo {} > data/stats.json

run:
	python3 src/main.py