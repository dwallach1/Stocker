from __future__ import unicode_literals, print_function

import logging
import warnings
from urllib.parse import urlparse
from bs4 import BeautifulSoup 
import datefinder
from dateutil.parser._parser import UnknownTimezoneWarning


from WebService import WebNode 
from RequestService import RequestHandler
import UtilityService as utility



logger = logging.getLogger(__name__)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)
logging.getLogger('datefinder').setLevel(logging.WARNING)

warnings.filterwarnings("ignore", category=UnknownTimezoneWarning)


class ArticleParser(object):
    """
     Steps:
        1. Takes in a URL
        2. Gets the content via the RequestService's RequestHandler
        3. Converts it to a Soup Object
        4. Cleans the soup object
        5. Converts it into a WebNode and returns the WebNode
    """
    
    def __init__(self, url, query, company_info, **kwargs):
        self.url = url
        self.source = query.source.lower()
        self.ticker = query.ticker.upper()
        self.requestHandler = RequestHandler()
        self.company_info = company_info
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.validate_request()
        logger.debug('Initalized ArticleParser for: {}'.format(url))
    
    def generate_web_node(self):
        """ Driver Function """
        web_node_args = {}
        
        soup, err = self.get_soup()
        if err:
            return None, err
        
        web_node_args['publishedDate'] = self.get_date(soup)
        web_node_args['title'] = self.get_title(soup)
        web_node_args['source'] = self.source
        web_node_args['url'] = self.url
        web_node_args['ticker'] = self.ticker
        for key, value in self.company_info.items():
            web_node_args[key] = value
        
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
        return (url_obj.scheme in valid_schemes) and ((url_obj.hostname == utility.source_translation(self.source)) or curious)
    
    def validate_output(self, webNode):
        """ """
        e_type = 'Required Field Exception'
        if not getattr(webNode, 'publishedDate', lambda: None):
            e = '{}: No Published Date Found'.format(e_type)
            logger.error(e)
            return False, e
        return True, None

    def get_soup(self):
        """Get URL's content and store it in a BeautfulSoup object"""
        resp, err = self.requestHandler.get(self.url)
        if err:
            e = 'Error getting URL contents: {}\nSkipping rest of process.'.format(err)
            logger.error(e) 
            return None, e
        return BeautifulSoup(resp.text, 'html.parser'), None
    
    def get_date(self, soup):
        """try to find an associated date of publishing"""
        date_path_config = {
            'bloomberg':    ('article', {}),
            'seekingalpha': ('article', {}),
            'reuters': ('div', {'class': 'ArticleHeader_date'}),
            'thestreet': ('time', {'title': 'Last Publish Date'}),
            'investopedia': ('div', {'id': 'displayed-date_1-0'}),
            'wsj':  ('time', {})
        }

        if self.source in date_path_config.keys():
            config = date_path_config[self.source]
            tag, attribute = config[0], config[1]
            date_holder = soup.find_all(tag, attribute)
        else:
            date_holder = [soup]

        date_string = None
        if len(date_holder):
            date_string = str(date_holder[0])

        logger.debug('Found date_string to be of type {}'.format(type(date_string)))
        
        if date_string:
            date_matches = datefinder.find_dates(date_string)
            try:
                date_match = next(date_matches)
                logger.debug('Date matches returned: {}'.format(date_match))
                return date_match.strftime("%Y-%m-%d")
            except StopIteration:
                logger.debug('Date matches returned: None.')
        return None

    def get_title(self, soup):
        """try to find an associated article title"""
        title_path_config = {
            'bloomberg':        ('h1', {'class': 'lede-text-v2__hed'}),
            'seekingalpha':     ('title', {}),
            'reuters':          ('h1', {'class': 'ArticleHeader_headline'}),
            'thestreet':        ('h1', {'class': 'article__headline'}),
            'investopedia':     ('h1', {'id': 'article-heading_2-0'}),
            'wsj':              ('h1', {'class': 'wsj-article-headline'})
        }
        config = title_path_config[self.source]
        tag, attribute = config[0], config[1]
        titles = soup.find_all(tag, attribute)
        title = None
        if len(titles):
            title = titles[0].getText()
        logger.debug('Title matches returned: {}'.format(title))
        if title:
            return ' '.join(title.split())
        return None