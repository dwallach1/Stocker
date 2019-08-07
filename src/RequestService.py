import requests
import logging
import time


GOOGLE_WAIT = 120 
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class RequestHandler():
    """handles making HTTP requests using request library"""
    
    def __init__(self, retries=4, backoff=[10, 20, 30, 60]):
        """ """
        self.retries = retries
        self.backoff = backoff
        self.headers = {	
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4'
        }
    
    def get(self, url):
        attempt = 0
        while (attempt < self.retries):
            req = requests.get(url, headers=self.headers)
            if (req.status_code == requests.codes.ok):
                return req, None
            # otherwise, log it and wait to retry
            logger.warn('recieved a non OK staus from: {}, waiting {} seconds'.format(url, self.backoff[attempt]))
            time.sleep(self.backoff[attempt])
            attempt += 1

        logger.error('Max retries ({}) attempted for {}'.format(attempt, url))
        return None, 'Max Retries Attempted'
