import json
import requests
import sys, getopt

from fasp.loc import crdcDRSClient, bdcDRSClient, Gen3DRSClient, anvilDRSClient
from fasp.loc import kfDRSClient
from fasp.loc import sdlDRSClient, SRADRSClient
from fasp.loc import sbcgcDRSClient, cavaticaDRSClient, sbbdcDRSClient
from fasp.loc import DRSClient
from fasp.loc import GA4GHRegistryClient



class DRSMetaResolver(DRSClient):
	'''simulate identifiers.org and n2t.net metaresolver capability.
	Prefixes used are not official. For demonstration purpposes only.
	
	Resolve compact ids
	Resolve host based DRS ids
	Send DRS calls to the correct server
	Handle id's prefixed with drs:// or not
	Handle Host URIs containing port no (DRS id specifies port should not be provided)'''
	
	# Initialize a DRS Client for the service at the specified url base
	# and with the REST resource to provide an access key 
	def __init__(self, debug=False, getReg=False, meta_resolver=None):
		crdcDRS = crdcDRSClient('~/.keys/crdc_credentials.json','s3')
		anvilDRS = anvilDRSClient('~/.keys/anvil_credentials.json', '', 'gs')
		bdcDRS = bdcDRSClient('~/.keys/bdc_credentials.json','gs')

		self.drsClients = { 
			"crdc": crdcDRS,
			"dg.4DFC": crdcDRS,
			"bdc": bdcDRS,
			"dg.4503": bdcDRS,
			"anv": anvilDRS,
			"dg.ANV0": anvilDRS,
			"sbcgc": sbcgcDRSClient('~/.keys/sbcgc_key.json','s3'),
			"sbcav": cavaticaDRSClient('~/.keys/sbcav_key.json','gs'),
			'sbbdc' : sbbdcDRSClient('~/.keys/sbbdc_key.json', 's3'),
			"sradrs": SRADRSClient('https://locate.be-md.ncbi.nlm.nih.gov', '~/.keys/dbgap_task-specific-token', '')
		}
			
		self.debug = debug
		self.meta_resolver = meta_resolver
		self.registeredClients = []

		self.hostNameIndex = {}		
		for k, cl in self.drsClients.items():
			host_name = cl.get_host()
			if self.debug: print(host_name)
			self.hostNameIndex[host_name] = cl
			
		if getReg: self.getRegisteredDRSServices()
		


	def __strip_schema(self, did):
		if did.startswith("drs://"):
			return did[6:]
		return did  # or whatever
		
	def get_object(self, colonPrefixedID):
		client, did = self.get_client_robust(colonPrefixedID)
		if client != None:
			#if self.debug: print('sending id {} to: {}'.format(id, client.__class__.__name__))
			if self.debug:
				print('sending id {} to: {}'.format(did, client.get_host()))
			return client.get_object(did)
		else:
			return "prefix unrecognized"
		
	def get_objects(self, drs_uri_list):
		responses = []
		for drs_id in drs_uri_list:
			drs_response = self.get_object(drs_id)
			responses.append(drs_response)
		return (responses)


	def get_access_url(self, colonPrefixedID, access_id=None):
		client, did = self.get_client_robust(colonPrefixedID)
		#client, id = self.get_client(colonPrefixedID)
		if client != None:
			return client.get_access_url(did, access_id)
		else:
			return "prefix unrecognized"
		
	def get_access_urls(self, access_id_list):
		urls = {}
		for drs_uri, access_id in access_id_list:
			url = self.get_access_url(drs_uri, access_id)
			urls[f"{drs_uri}-{access_id}"] = url
		return (urls)
							
	def get_client(self, submittedID):
		
		colonPrefixedID = self.__strip_schema(submittedID)
		
		idParts = colonPrefixedID.split(":", 1)
		prefix = idParts[0]
		if prefix in self.drsClients.keys():
			return self.drsClients[prefix] , idParts[1]
		else:
			return None
			
	def get_client_robust(self, submittedID):
		''' find the DRS client for any kind of id we might be sent  '''
		
		stripped_id = self.__strip_schema(submittedID)
		# is it compact or host based?
		if ":" in stripped_id:
			# It could still be host:port - let's check
			# Note that the DRS spec saya port should not be in
			idParts = stripped_id.split(":", 1)
			prefix = idParts[0]
			if prefix in self.drsClients.keys():
				# known prefix - get the client
				return self.drsClients[prefix] , idParts[1]
			else:
				if self.debug: print(f"Not a recognized prefix")
		
		# Deal with host based ids
		idParts = stripped_id.split("/")
		host = idParts[0]
		if host in self.hostNameIndex:
			return self.hostNameIndex[host], idParts[1]
		else:
			host_url =f"http://{host}"
			if self.debug: print(f"Adding  DRS client for {host}")
			self.hostNameIndex[host] = DRSClient(host_url)
			return self.hostNameIndex[host], idParts[1]
			
	def getRegisteredClient(self, colonPrefixedID):
		idParts = colonPrefixedID.split(":", 1)
		prefix = idParts[0]
		
		if prefix in self.registeredClients.keys():
			return [self.registeredClients[prefix] , idParts[1]]
		else:
			return None
			
	def DRSClientFromRegistryEntry(self, service, prefix):
		
			if prefix == "crdc": 
				drsClient = crdcDRSClient('~/.keys/crdc_credentials.json','s3')
			elif prefix == "bdc": 
				drsClient = bdcDRSClient('~/.keys/bdc_credentials.json','gs')
			elif prefix == "insdc": 
				drsClient = sdlDRSClient('~/.keys/prj_11218_D17199.ngc')
			elif prefix == "sbcgc": 
				drsClient = sbcgcDRSClient('~/.keys/sevenbridges_keys.json','s3')
			elif prefix == "sbcav": 
				drsClient = cavaticaDRSClient('~/.keys/sevenbridges_keys.json','s3')
			elif service['url'] == "https://data.kidsfirstdrc.org":
				drsClient = kfDRSClient('~/.keys/kf_credentials.json')				
			else: 
				drsClient = DRSClient.fromRegistryEntry(service)
			return drsClient

			
	# Look for registered DRS services
	def getRegisteredDRSServices(self):
		reg = GA4GHRegistryClient(debug=self.debug)
		drsServices = reg.getRegisteredServices('org.ga4gh:drs')
		#if ('message', 'Service Unavailable') in drsServices.items():
		if not isinstance(drsServices, list):
			print('GA4GH registry unavailable, cannot get registered DRS services.')
			print('Continuing with locally known DRS services.')
			return None

		for service in drsServices:
			if self.debug:
				json.dumps(service, indent=3)
			serviceURL = service['url']
			if 'curiePrefix' in service:
				prefix = service['curiePrefix']
			else:
				prefix = None
			drsClient = self.DRSClientFromRegistryEntry(service, prefix)
			hostname = serviceURL.split("/")[2]
			self.registeredClients.append(drsClient)
			self.hostNameIndex[hostname] = drsClient
			self.drsClients[prefix] = drsClient
			if self.debug:
				print('__________________________')
				print("id:{}".format(service['id']))
				print (drsClient.id, drsClient.name)
				print("url:{}".format(serviceURL))
				print("prefix:{}".format(prefix))
		return None
	
	def checkResolution(self, meta_resolver=None):
		mixedIDs = [
				'bdc:66eeec21-aad0-4a77-8de5-621f05e2d301',
				'dg.4503:66eeec21-aad0-4a77-8de5-621f05e2d301',
				'crdc:0e3c5237-6933-4d30-83f8-6ab721096bc7',
				'dg.4DFC:0e3c5237-6933-4d30-83f8-6ab721096bc7',
				'sbcgc:5baa8913e4b0db63859e515e',
				'sbcav:5772b6ed507c1752674486fc',
				'anv:895c5a81-b985-4559-bc8e-cecece550756',
				'dg.ANV0:895c5a81-b985-4559-bc8e-cecece550756',
				'sradrs:72ff6ff882ec447f12df018e6183de59']

	
		testResults = {}
		for id in mixedIDs:
			print('-------------------------------')
			print('sending: {}'.format(id))
			if meta_resolver:
				res = self.get_object(id)
			else:
				res = self.get_object(id)
			idParts = id.split(":", 1)
			if res == 400:
				testResults[idParts[0]] = 'request error'.format(id)
			if res == 404:
				testResults[idParts[0]] = 'id not found:{}'.format(id)
			elif res == 401:
				testResults[idParts[0]] = 'Unauthorized'
			elif res == 500:
				testResults[idParts[0]] = 'server error - may be unauthorized'
			elif res == 502:
				testResults[idParts[0]] = 'proxy error 502'
			elif res.__class__.__name__ != int:
				testResults[idParts[0]] = 'Success'
				print(json.dumps(res, indent=2))
			else: 
				testResults[idParts[0]] = 'Failed: response was {}'.format(res)
			
		print('----Test results ---')
		for clientKey in self.drsClients.keys():
			if clientKey in testResults:
				print ("{} Tested: {}".format(clientKey, testResults[clientKey]))
			else:
				print ("{} untested".format(clientKey))
			
	def checkHostURIResolution(self):
		mixedIDs = ['drs://gen3.theanvil.io/737247da-f5da-49a7-86ec-737978eb8293',
				'drs://gen3.biodatacatalyst.nhlbi.nih.gov/65f34e96-230a-4e20-b15d-8510d688cbf0',
				'drs://nci-crdc.datacommons.io/ff59c94b-8124-48a8-8b78-72e71f5d71f0',
				]
	
		for id in mixedIDs:
			print('-------------------------------')
			print(id)
			res = self.get_object(id)
			print(json.dumps(res, indent=2))	

def usage():
	print (sys.argv[0] +' -h -c -u')

def main(argv):

	mr = DRSMetaResolver()

	try:
		opts, args = getopt.getopt(argv, "hcu", ["help", "checkCompactResolution", "checkURIResolution"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
	    if opt in ("-h", "--help"):
	        usage()
	        sys.exit()
	    elif opt in ("-c", "--checkCompactResolution"):
	        mr.checkResolution()
	    elif opt in ("-u", "--checkURIResolution"):
	        #mr.getRegisteredDRSServices()
	        mr.checkHostURIResolution()


			
if __name__ == "__main__":
    main(sys.argv[1:])

