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
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9,fr;q=0.8,ro;q=0.7,ru;q=0.6,la;q=0.5,pt;q=0.4,de;q=0.3',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
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
