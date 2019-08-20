import sys
import re

from collections import namedtuple
Query = namedtuple('Query', 'ticker source string')

def querify(ticker, source, string): 
    return Query(ticker, source, '+'.join(string.split(' ')))

def sysprint(text):
    """moves cursor down one line -- prints over the current line -- then back up one line"""
    sys.stdout.write('\033[1B\r{}\033[K\033[1A'.format(text))
    sys.stdout.flush()

def source_translation(name, host=True):
    """
    finds a correlating hostname or source for a name input
    returns -> string on success, None on error
    :param name: the full host name or the source name
    :type name: string
    :param host: tells which dict to use 
    :type host: boolean
    """
    hosts = {
        'motleyfool': 	'www.fool.com',
        'bloomberg': 	'www.bloomberg.com',
        'seekingalpha': 'seekingalpha.com',
        'yahoofinance': 'finance.yahoo.com',
        'investopedia': 'www.investopedia.com',
        'investing':	'www.investing.com',
        'marketwatch': 	'www.marketwatch.com',
        'googlefinance': 'www.google.com',
        'reuters': 		'www.reuters.com',
        'thestreet': 	'www.thestreet.com',
        'msn':			'www.msn.com',
        'wsj':			'www.wsj.com',
        'barrons':		'www.barrons.com',
        'zacks':		'www.zacks.com',
        'investorplace':'investorplace.com',
        'benzinga':		'www.benzinga.com'

    }
    sources = {v: k for k, v in hosts.items()}
    bucket = hosts if host else sources 
    if not (name in bucket.keys()): return None
    return bucket[name.lower()]

def get_valid_sources(): 
    """returns a list of sources which this project has been optimized for"""
    # investopedia is optimized, but cannot find date --> opened issue: https://github.com/akoumjian/datefinder/issues/113
    return ['bloomberg', 'seekingalpha', 'reuters', 'thestreet', 'wsj']