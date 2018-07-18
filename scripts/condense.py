import csv



lines = []

with open('data/static/NASDAQ_companylist.csv') as csv_file:
	csv_reader = csv.reader(csv_file, delimiter=',')
	i = 0
	for row in csv_reader:
		if i == 0:
			i += 1
		else:
			line = row[0] + ',' + row[1].split(',')[0] + ',' + row[6] + ',' + row[7] + '\n'
			lines.append(line)



with open('data/static/NYSE_companylist.csv') as csv_file:
	csv_reader = csv.reader(csv_file, delimiter=',')
	i = 0
	for row in csv_reader:
		if i == 0:
			i += 1
		else:
			line = row[0] + ',' + row[1].split(',')[0] + ',' + row[6] + ',' + row[7] + '\n'
			lines.append(line)



csv_file = open('condensed.csv', 'w')
headers = 'Symbol, Name, Sector, Industry\n'
csv_file.write(headers)

for line in lines:
	csv_file.write(line)