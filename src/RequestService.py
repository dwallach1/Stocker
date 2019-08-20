import requests
import logging
import time
from bs4 import BeautifulSoup 

GOOGLE_WAIT = 120 
PROXY_CODES = [403, 429]
OK = lambda status: (status == '200 OK' or status == '200 - OK' or status == requests.codes.ok)

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class RequestHandler():
    """handles making HTTP requests using request library"""
    
    def __init__(self, retries=4, backoff=[10, 20, 30, 60], proxies=5):
        """ """
        self.retries = retries
        self.backoff = backoff
        self.proxies = proxies

        # https://medium.com/@speedforcerun/python-crawler-http-error-403-forbidden-1623ae9ba0f
        # https://stackoverflow.com/questions/48756326/web-scraping-results-in-403-forbidden-error
        self.headers = {	
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9,fr;q=0.8,ro;q=0.7,ru;q=0.6,la;q=0.5,pt;q=0.4,de;q=0.3',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
            }
    
    def generate_proxies(self):
        """ """
        url = 'https://free-proxy-list.net/'
        try:    
            resp, err = self.get(url)
        except:
            return None, 'Error (likely connection reset by peer)'
        if err:
            e = 'Error parsing proxy list from {}'.format(url)
            return None, e
        soup = BeautifulSoup(resp.text, 'html.parser')
        tbody = soup.find('tbody')
        trs = tbody.find_all('tr')
        proxies = []
        for tr in trs:
            tds = tr.find_all('td')
            ip, port = tds[0].get_text(), tds[1].get_text()
            proxies.append((ip, port))
        return proxies[:self.proxies], None

    def get(self, url, headers=None):
        if headers == None:
            headers = self.headers
        attempt = 0
        proxy = False
        while (attempt < self.retries):
            if proxy:
                proxies, err = self.generate_proxies()
                if err:
                    return None, err
                for proxy in proxies:
                    try:
                        logger.debug('Trying proxy: {}'.format(proxy))
                        req = requests.get(url, proxies={
                                                    'https': '{}:{}'.format(proxy[0], proxy[1])
                                        }, headers=headers)
                        if OK(req.status_code):
                            logger.debug('Successfully got data through proxy request.')
                            return req, None
                        else:
                            logger.error('Error using proxy service with proxy.')
                    except:
                        logger.error('Error using proxy service with proxy.')
                return None, 'Hit proxy Error, then exhausted proxy tries'

            req = requests.get(url, headers=headers)
            if OK(req.status_code):
                return req, None
            # otherwise, log it and wait to retry
            logger.warn('recieved a non OK staus ({}) from: {}, waiting {} seconds'.format(req.status_code, url, self.backoff[attempt]))
            if req.status_code in PROXY_CODES:
                logger.debug('turning on proxy request because we detected {}'.format(req.status_code))
                proxy = True
                continue

            time.sleep(self.backoff[attempt])
            attempt += 1

        logger.error('Max retries ({}) attempted for {}'.format(attempt, url))
        return None, 'Max Retries Attempted'
    
    def post(self, url, data, headers=None):
        """ """
        if headers == None:
            headers = self.headers
        req = requests.post(url, json=data, headers=headers)
        err = None
        if OK(req.status_code):
            err = "recieved a non OK staus ({}) from: {}.".format(req.status_code, url)
        return req.json(), err