from __future__ import unicode_literals, print_function, division
import sys
import os 

dir_path = os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) )
sys.path.append(dir_path + '/src')

from CrawlerService import Stocker

# initalize dummy worker
worker = Stocker(None, None, None)


def is_homepage_test():
    cases = [
        ({'url': 'http://www.bloomberg.com/quote/SAP:US',   'source': 'bloomberg'}, True),
        ({'url': 'http://www.bloomberg.com/quote/SAP:GR',   'source': 'bloomberg'}, True),
        ({'url': 'http://www.bloomberg.com/quote/SAP',      'source': 'bloomberg'}, False),
        ({'url': 'http://www.bloomberg.com/quote/SAP2:GR',  'source': 'bloomberg'}, False),
        ({'url': 'http://www.bloomberg.com/quotes/SAP:GR',  'source': 'bloomberg'}, False),        
    ]

    for c in cases:
        outcome = worker.is_homepage(**(c[0]))
        if outcome != c[1]:
            print ( 'Error Evaluating HomePageTest. Incorrect outcome for case: {}'.format(c) )
            return

    print ('    is_homepage_test ... PASSED')
    return 

def is_of_source_test():
    cases = [
        ({'url': 'http://www.bloomberg.com/quote/SAP:US',   'source': 'bloomberg'}, True),
        ({'url': 'http://www.bloomberg.com/quote/SAP:GR',   'source': 'bloomberg'}, True),
        ({'url': 'http://www.bloomberg.com/quotes/SAP:GR',  'source': 'yahoo'}, False),   
        ({'url': 'http://seekingalpha.com/article/4243142-sap-growth-without-limit-growing-dividend',  'source': 'seekingalpha'}, True),         
    ]

    for c in cases:
        outcome = worker.is_of_source(**(c[0]))
        if outcome != c[1]:
            print ( 'Error Evaluating is_of_source_test. Incorrect outcome ({}) for case: {}'.format(outcome, c) )
            return

    print ('    is_of_source_test ... PASSED')
    return 


print ('Testing Module CrawlerService')
print ('-----------------------------')
is_homepage_test()
is_of_source_test()