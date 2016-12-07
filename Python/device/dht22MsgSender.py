#!/usr/bin/python
import sys
import Adafruit_DHT
import datetime
import json

import base64
import hmac
import hashlib
import time
import requests
import urllib

class DHT22MsgSender:
    
    API_VERSION = '2016-02-03'
    TOKEN_VALID_SECS = 10
    TOKEN_FORMAT = 'SharedAccessSignature sig=%s&se=%s&skn=%s&sr=%s'
    
    def __init__(self, connectionString=None):
        if connectionString != None:
            iotHost, keyName, keyValue = [sub[sub.index('=') + 1:] for sub in connectionString.split(";")]
            self.iotHost = iotHost
            self.keyName = keyName
            self.keyValue = keyValue
            
    def _buildExpiryOn(self):
        return '%d' % (time.time() + self.TOKEN_VALID_SECS)
    
    def _buildIoTHubSasToken(self, deviceId):
        resourceUri = '%s/devices/%s' % (self.iotHost, deviceId)
        targetUri = resourceUri.lower()
        expiryTime = self._buildExpiryOn()
        toSign = '%s\n%s' % (targetUri, expiryTime)
        key = base64.b64decode(self.keyValue.encode('utf-8'))
        signature = urllib.quote(
            base64.b64encode(
                hmac.HMAC(key, toSign.encode('utf-8'), hashlib.sha256).digest()
            )
        ).replace('/', '%2F')
        return self.TOKEN_FORMAT % (signature, expiryTime, self.keyName, targetUri)
    
    def sendD2CMsg(self, deviceId, message):
        sasToken = self._buildIoTHubSasToken(deviceId)
        url = 'https://%s/devices/%s/messages/events?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.post(url, headers={'Authorization': sasToken}, data=message)
        return r.status_code #r.text, r.status_code
    
if __name__ == '__main__':
    # Setup Azure IOT Hub Connection
    connectionString = 'HostName=Sri-Home-Iot-Hub.azure-devices.net;SharedAccessKeyName=device;SharedAccessKey=t07p+HDAVS8DnNsEGwmCaM3aZEObarkQk+H51GduDKM='
    #connectionString = 'HostName=Sri-Home-Iot-Hub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=4JNd69iePfvjn1sNHW4afxCey6Gk8IORmwFfzfDE2as='
    dht22MsgSender = DHT22MsgSender(connectionString)
    deviceId = 'rpia'

    # Set up the required variables for the sensor
    Dht_Type = Adafruit_DHT.DHT22
    Dht_Pin  = 14

    while True:
    	# Get reading from the sensor. Repeat rest of the code in a loop.
    	humid, temp = Adafruit_DHT.read_retry(Dht_Type, Dht_Pin)

    	# Create the JSON message
    	Json_Message = '{\"temperature\" : ' + str(temp) + ', \"humidity\" : ' + str(humid) + '}'
    	print Json_Message

    	# Send the json message to Azure IOT Hub
    	res = dht22MsgSender.sendD2CMsg(deviceId, json.dumps(Json_Message))
    	if res == 204:
		print Json_Message
    	else:
		print 'message send failed'
		print res
	
	time.sleep(15)	# Sleep for 15 seconds
