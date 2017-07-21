hdr = sorted(['ticker','sector','industry','article','url', 'pubdate', 'sentences','words', 'polarity','subjectivity','negative','positive','priceT0','priceT1','priceT2','priceT3','priceT4','priceT5'])


from pandas import read_csv

df = read_csv('../data/examples.csv')
df.columns = hdr
df.to_csv('../data/examples_2.csv')