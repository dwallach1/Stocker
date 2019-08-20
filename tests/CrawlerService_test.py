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
        ({'url': 'https://www.reuters.com/finance/stocks/overview/SAP', 'source': 'reuters'}, True),   
        ({'url': 'https://www.reuters.com/finance/stocks/company-news/SAP', 'source': 'reuters'}, True),  
        ({'url': 'https://www.reuters.com/article/us-sap-results/sap-says-big-margin-gains-to-wait-until-2020-shares-down-10-idUSKCN1UD0F8', 'source': 'reuters'}, False),  
        ({'url': 'https://www.reuters.com/finance/stocks/analyst/SAP', 'source': 'reuters'}, True),  
        ({'url': 'https://www.reuters.com/finance/stocks/chart/SAPG.DE', 'source': 'reuters'}, True),  
        ({'url': 'https://www.reuters.com/finance/stocks/companyProfile/SAPG.DE', 'source': 'reuters'}, True),  
        ({'url': 'https://www.thestreet.com/quote/SAP/details/news.html', 'source': 'thestreet'}, True),     
        ({'url': 'https://www.thestreet.com/press-releases/leading-companies-around-the-globe-continue-to-choose-sap-reg-ariba-reg-and-sap-fieldglass-reg-solutions-for-intelligent-spend-management-15056741', 'source': 'thestreet'}, False),          
        ({'url': 'https://www.investopedia.com/7-tech-companies-that-may-get-bought-next-in-tech-m-and-a-spree-4690575', 'source': 'investopedia'}, False),     
   
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
        ({'url': 'https://www.reuters.com/finance/stocks/overview/SAP', 'source': 'reuters'}, True),
        ({'url': 'https://www.thestreet.com/quote/SAP/details/news.html', 'source': 'thestreet'}, True),
        ({'url': 'https://www.investopedia.com/7-tech-companies-that-may-get-bought-next-in-tech-m-and-a-spree-4690575', 'source': 'investopedia'}, True),              
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