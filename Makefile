.PHONY: clean run

clean:
	pip freeze > requirements.txt
	rm -rf data
	mkdir data
	echo {} > data/data.json
	echo {} > data/urls.json
	echo {} > data/stats.json
	

run:
	python3 src/main.py

test:
	python3 tests/CrawlerService_test.py