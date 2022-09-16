# iRODS DRS Implementation

## Test Data Standup

NOTE: Testing procedures here are provisional, requiring a local iRODS configuration. This assumes
the user is utilizing the Docker compose framework found here: https://github.com/NIEHS/irods-data-repository-service/blob/master/ga4gh-drs-service/compose/RUNNING.md

As this is prepared to integrate, we can investigate an accessible cloud deployment
that can be used for demonstrations and client testing without requiring setup.

The following notes and associated configuration data can be used in the
meantime.

## Stand up docker compose

Use the procedures in the iRODS DRS client compose and configure a DRS bundle
via the DRS console using these instructions: 

https://github.com/NIEHS/irods-data-repository-service/blob/master/ga4gh-drs-service/compose/RUNNING.md

Copy the DRS bundle into the irods_credentials.json provided and
place in the irods.json file in folder in your home directory called .keys

In the interim, the irods_credentials.json file will include both the
basic auth user id and password used to obtain a bearer token, it will
include the drs bundle id to use in the test code.

The test standup therefore requires the use of the drs console in the above
iRODS procedures to build and obtain the bundle id. The iRODS compose framework
will need to be running for the test to run.

TODO: replace with a network-available test bundle

##

irods-credentials.json format:

```json
{
 
  "user": "test1",
  "password": "test",
  "drs_bundle_id": "ADD FROM CONSOLE",
  "auth_url": "http://localhost:8888/token",
  "api_url": "http://localhost:8080/ga4gh/drs/v1/"
  
}


```