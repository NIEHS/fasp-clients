import requests
import json
import os.path
from requests.auth import HTTPBasicAuth
import logging
from DRSClient import DRSClient

logging_level = logging.INFO


class IrodsDRSClient(DRSClient):
    '''Generic iRODS DRS Client for on-prem operations'''

    # Initialize a DRS Client for the service at the specified url base
    # and with the REST resource to provide an access key, this is done via
    # an auth call to the iRODS REST API 
    def __init__(self, api_url_base, auth_url, user_name, password,
                 access_id=None, debug=False):

        super().__init__(api_url_base, access_id, debug=debug)
        self.api_key = None
        self.auth_url = auth_url
        self.user_name = user_name
        self.password = password
        self.bearer_token = None

    def authorize(self):
        headers = {'Content-Type': 'application/json'}
        request_auth = HTTPBasicAuth(username=self.user_name, password=self.password)
        payload_tuples = {''}
        response = requests.post(self.api_url, headers=headers, params=payload_tuples)

        if response.status_code == 200:
            self.bearer_token = response.content
            self.authorized = True
        else:
            self.authorized = False
            self.bearer_token = None

        return response.status_code

    def get_access_url(self, object_id, access_id=None):
        if not self.authorized:
            self.authorize()
        return DRSClient.get_access_url(self, object_id, access_id=access_id)


if __name__ == "__main__":

    filepath = os.path.expanduser('~/.keys/irods_credentials.json')
    if not os.path.exists(filepath):
        logging.error(f"{filepath} does not exist")
    else:
        with open(filepath) as f:
            cfg = json.load(f)
            #api_url_base, auth_url, user_name, password,access_id=None, debug=False)
            drsClient =  IrodsDRSClient(cfg['api_url'], cfg['auth_url'], cfg['user'], cfg['password'])
            drs_id = cfg['drs_bundle_id']
            logging.INFO("drs id:%s" % drs_id)

            res = drsClient.get_object(drs_id)
            logging.INFO('GetObject for %s' % drs_id)
            logging.INFO(json.dumps(res, indent=3))
            # Get and access URL
            try:
                url = drsClient.get_access_url(drs_id)
                logging.INFO(f'URL for {drs_id}')
            except:
                if not drsClient.authorized:
                    print(
                        "This DRS client has not obtained authorization "
                        "and cannot obtain URLs for controlled access objects")
                else:
                    print("You may not have authorization for this object")

