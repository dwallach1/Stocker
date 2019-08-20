
import logging

from RequestService import RequestHandler
import UtilityService as utility
 

logger = logging.getLogger(__name__)

class QualtricsHandler(object):
    """group of methods to interact with Qualtrics"""

    def __init__(self, token, datacenter, surveyID, poolId=None, verbose=True):
        self.requestHandler = RequestHandler()
        self.verbose = verbose       
        self.datacenter = datacenter
        self.surveyID = surveyID
        self.token = token
        self.poolId = poolId
        self.headers = {
            'X-API-TOKEN':      token,   
            'content-type':     'application/json'
        }

    def submit_node(self, webNode):
        """Post the Web Node to as a new response"""
        url = "https://{}.qualtrics.com/API/v3/surveys/{}/responses".format(self.datacenter, self.surveyID)
        data = {
            "values": dict(webNode)
        }
        logger.info('trying to send response to Qualtrics ({})\n{}'.format(url, data))
        resp, err = self.requestHandler.post(url, data, headers=self.headers)
        logger.debug('RequestID from Qualtrics: {}'.format(resp['meta']['requestId']))
        if err:
            logger.error('Error posting response to Qualtrics: {}'.format(resp))
        return None

