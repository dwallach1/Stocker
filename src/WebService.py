class WebNode(object):
	"""represents an entry in data.csv that will be used to train the sentiment classifier"""
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
      			setattr(self, key, value)
	
	def __iter__(self):
		attrs = [attr for attr in dir(self) if attr[:2] != '__']
		for attr in attrs:
			yield attr, getattr(self, attr)
			  
	def __dict__(self):
		""" """
		return {
			'publishedDate': 	self.publishedDate,
			'title': 			self.title
		}