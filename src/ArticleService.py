from __future__ import unicode_literals, print_function

import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup 
import datefinder


from WebService import WebNode 
from RequestService import RequestHandler
from HelperService import Helper

logger = logging.getLogger(__name__)


class ArticleParser(object):
    """
     Steps:
        1. Takes in a URL
        2. Gets the content via the RequestService's RequestHandler
        3. Converts it to a Soup Object
        4. Cleans the soup object
        5. Converts it into a WebNode and returns the WebNode
    """
    
    def __init__(self, url, source, **kwargs):
        self.url = url
        self.source = source
        self.requestHandler = RequestHandler()
        self.helper = Helper()
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.validate_request()
        logger.debug('Initalized ArticleParser for: {}'.format(url))
    
    def generate_web_node(self):
        """ Driver Function """
        web_node_args = {}
        
        soup = self.get_soup()
        
        published_date = self.get_date(soup)
        web_node_args['publishedDate'] = published_date
        
        webNode = WebNode(**web_node_args)
        _ , err = self.validate_output(webNode)
        if err:
            return None, err
        
        return webNode, None

    def validate_request(self):
        """Checks against the flags the object was initalized with and ensures everything is valid"""
        
        if hasattr(self, 'validate_url'):
            if getattr(self, 'validate_url') and (not self.is_valid_url()):
                err = 'url was invalid and the flag validate_url was set to true. Aborting.'
                logger.error(err)
                return None, err
        
    def is_valid_url(self):
        """Checks if the URL is structurally correct and of the correct source [unless the curious flag is set]"""
        url_obj = urlparse(self.url)
        if not url_obj: 
            logger.warn('url_obj unable to parse url for url {}'.format(self.url))
            return False
        
        valid_schemes = ['http', 'https']
        curious = False
        if hasattr(self, 'curious'):
            curious = getattr(self, 'curious')
        if not url_obj.hostname: 
            return False
        return (url_obj.scheme in valid_schemes) and ((url_obj.hostname == self.helper.source_translation(self.source)) or curious)
    
    def validate_output(self, webNode):
        """ """
        e_type = 'Required Field Exception'
        if not getattr(webNode, 'publishedDate', lambda: None)():
            e = '{}: No Published Date Found'.format(e_type)
            logger.error(e)
            return False, e
        return True, None

    def get_soup(self):
        """Get URL's content and store it in a BeautfulSoup object"""
        resp, err = self.requestHandler.get(self.url)
        if err:
            logger.err('Error getting URL contents: {}\nSkipping rest of process.', err) 
        return BeautifulSoup(resp.text, 'html.parser')
    
    def get_date(self, soup):
        """try to find an associated date of publishing"""
        date_matches = list(datefinder.find_dates(soup.prettify()))
        if len(date_matches):
            return date_matches[0]
        return None