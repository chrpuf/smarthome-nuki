#!/usr/bin/env python3

import urllib.request
import requests
import json

from datetime import datetime
startTime = datetime.now()

ip = '192.168.0.7'
port = '8080'
token = 'jEh5eH'
nukiId = '60928385'
protocol = 'http'
action = ''
noWait = ''

baseURL = protocol + '://' + ip + ":" + port + '/'
lockActions = {"unlock" : "1",	
               "lock" : "2", 
               "unlatch" : "3",
               "lockAndGo" : "4",
               "lockAndGoWithUnlatch" : "5"}

lockStates = {"0" : "uncalibrated",
              "1" : "locked",
              "2" : "unlocking",
              "3" : "unlocked",
              "4" : "locking",
              "5" : "unlatched",
              "6" : "unlocked(lockAndGo)",
              "7" : "unlatching",
              "254" : "motor blocked",
              "255" : "undefined"}

def apiCall(baseURL, endpoint, nukiId, token, action, noWait):
	request = urllib.request.urlopen(baseURL + endpoint + '?nukiId=' + nukiId + '&token=' + token + '&action=' + action + '&noWait=' + noWait  )
	encoding = request.info().get_content_charset('utf-8')
	data = request.read().decode(encoding)
	return json.loads(data)

JSON_object = apiCall(baseURL, 'lockState', nukiId, token, action, noWait)

print(JSON_object)
#print(JSON_object['stateName'])
print(datetime.now() - startTime)


