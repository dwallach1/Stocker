import pandas as pd

def read_pd():
	perf = pd.read_pickle('dma.pickle') # read in perf DataFrame
	perf.head()
	return perf



import matplotlib.pyplot as plt

def graph_pd(perf):
	ax1 = plt.subplot(211)
	perf.portfolio_value.plot(ax=ax1)
	ax1.set_ylabel('portfolio value')
	ax2 = plt.subplot(212, sharex=ax1)
	perf.AAPL.plot(ax=ax2)
	ax2.set_ylabel('AAPL stock price')


perf = read_pd()
graph_pd(perf)