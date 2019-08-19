
class WebNode(object):
	"""represents an entry in data.csv that will be used to train the sentiment classifier"""
	def __init__(self, 	title, 
						publishedDate, 
						source, 
						ticker, 
						url,
						industry,
						sector):
		self.ArticleName = title
		self.PublishDate = publishedDate
		self.NewsSource = source
		self.Ticker = ticker
		self.Url = url
		self.Industry = industry
		self.Sector = sector
			
	def __iter__(self):
		attrs = [attr for attr in dir(self) if attr[:2] != '__']
		for attr in attrs:
			yield attr, getattr(self, attr)
