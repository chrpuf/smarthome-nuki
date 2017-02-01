#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import urllib.request
import json
import lib.connection
import socket
import re



logger = logging.getLogger('')
pairedNukiLocks = []
nukiLocks = {}
nukiLocksBatteryState = {}

class NukiTCPDispatcher(lib.connection.Server):
    def __init__(self, ip, port):
        lib.connection.Server.__init__(self, ip, port, proto='TCP')
        self.dest = 'tcp:' + ip + ':{port}'.format(port=port)
        logger.debug('starting tcp listener with {url}'.format(url=self.dest))

        self.connect()


    def handle_connection(self):
        try:
            conn, address = self.socket.accept()
            data = conn.recv(1024)
            address = "{}:{}".format(address[0], address[1])
            logger.info("{}: incoming connection from {}".format('test', address))
        except Exception as err:
            logger.error("{}: {}".format(self._name, err))
            return

        try:
            result = re.search('\{.*\}',data.decode('utf-8'))
            logger.debug('Nuki Getting JSON String')
            strJSON = result.group(0)
            nukiBridgeResponse = json.loads(strJSON)
            logger.debug("Status Nuki Smartlock: ID: " + str(nukiBridgeResponse['nukiId']) + " Status: " + nukiBridgeResponse['stateName'])
            
            conn.send(b"HTTP/1.1 200 OK\nContent-Type: text/html\n\n")
        

            
            for item in nukiLocks:
                if int(nukiLocks[item]) == int(nukiBridgeResponse['nukiId']):
                    logger.debug('Found Nuki Lock for updating lockState via Callback')
                    item(nukiBridgeResponse['stateName'], 'NUKI')
                    break            



        except Exception as err:
            logger.error("Error parsing sonos broker response!\nError: {}".format(err))

class Nuki():

    def __init__(self, smarthome, bridge_ip, bridge_port, bridge_api_token, bridge_callback_ip="", bridge_callback_port=8090, protocol='http'):
        
        

        self._sh = smarthome
        self._baseURL = protocol + '://' + bridge_ip + ":" + bridge_port + '/'
        self._token = bridge_api_token
        self._callback_ip = bridge_callback_ip
        self._callback_port = bridge_callback_port
        self._action = ''
        self._noWait = ''


        if not self._callback_ip:
            self._callback_ip = get_lan_ip()

            if not self._callback_ip:
                logger.critical("Could not fetch internal ip address. Set it manually!")
                self.alive = False
                return
            logger.info("using local ip address {ip}".format(ip=self._callback_ip))
        else:
            logger.info("using given ip address {ip}".format(ip=self._callback_ip))

        self._lockActions = {"unlock" : "1",  
               "lock" : "2", 
               "unlatch" : "3",
               "lockAndGo" : "4",
               "lockAndGoWithUnlatch" : "5"}

        self._lockStates = {"0" : "uncalibrated",
              "1" : "locked",
              "2" : "unlocking",
              "3" : "unlocked",
              "4" : "locking",
              "5" : "unlatched",
              "6" : "unlocked(lockAndGo)",
              "7" : "unlatching",
              "254" : "motor blocked",
              "255" : "undefined"}

        callbackUrl = "http://" + self._callback_ip + ":" + self._callback_port + "/"

        #Setting up the callback URL
        if self._callback_ip != "": 
            callbacks = self._apiCall(self._baseURL, 'callback/list', '', self._token, '', '', '')
            for c in callbacks['callbacks']:
                if c['url'] == callbackUrl:
                    found = True
            if found != True:
                response = self._apiCall(self._baseURL, 'callback/add', '', self._token, '', '', callbackUrl)
                if response['success'] != 'true':
                    logger.warning('Error establishing the callback url')
                else:
                    logger.info('Callback URL registered. Starting TCP dispatcher...')
                    NukiTCPDispatcher(self._callback_ip, self._callback_port)
            else:
                logger.info('Callback URL already registered. Starting TCP dispatcher...')
                NukiTCPDispatcher(self._callback_ip, self._callback_port)        
        else:
            logger.warning('No callback ip set. Automatic Nuki lock status updates not available.')

        #Getting Nuki Locks already paired with Nuki Bridge
        response = self._apiCall(self._baseURL, 'list', '', self._token, '', '', '')
        for r in response:
            pairedNukiLocks.append(str(r['nukiId']))
            logger.info('Paired Nuki Lock found: Name: ' + r['name'] ', nukiId: ' + str(r['nukiId']))
        logger.debug(pairedNukiLocks)

    def run(self):
        self.alive = True
        logger.info("Initializing Nuki Status")
        for item in nukiLocks:
          response = self._apiCall(self._baseURL, 'lockState', nukiLocks[item], self._token, self._action, self._noWait, '')
          item(response['stateName'], 'NUKI')
          for itemBat in nukiLocksBatteryState:
            if nukiLocksBatteryState[itemBat] == nukiLocks[item]:
                itemBat(response['batteryCritical'], 'NUKI')
        # if you want to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'nukiId' in item.conf:
            logger.debug("parse item: {0}".format(item))
            if item.conf['nukiId'] in pairedNukiLocks:
                nukiLocks[item] = item.conf['nukiId']
                return self.update_item
            else:
                logger.warning('Nuki id ' + item.conf['nukiId'] + ' not within reach of the Nuki Bridge')
        elif 'nukiBatteryState' in item.conf:
            logger.debug("parse item: {0}".format(item))
            nukiLocksBatteryState[item] = item.conf['nukiBatteryState']
        else:
            return None

    def parse_logic(self, logic):
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'plugin':
            if item() in self._lockActions:
              self._action = self._lockActions[item()]
              response = self._apiCall(self._baseURL, 'lockAction', nukiLocks[item], self._token, self._action, self._noWait, '')
              self._action = ''
              if response['success'] == True:
                response = self._apiCall(self._baseURL, 'lockState', nukiLocks[item], self._token, self._action, self._noWait, '')
                item(response['stateName'], 'NUKI')
                for itemBat in nukiLocksBatteryState:
                    if nukiLocksBatteryState[itemBat] == nukiLocks[item]:
                        itemBat(response['batteryCritical'], 'NUKI')
            logger.info("update item: {0}".format(item.id()))

    def _apiCall(self, baseURL, endpoint, nukiId, token, action, noWait, callbackUrl):
        request = urllib.request.urlopen(baseURL + endpoint + '?nukiId=' + nukiId + '&token=' + token + '&action=' + action + '&noWait=' + noWait + '&url=' + callbackUrl)
        encoding = request.info().get_content_charset('utf-8')
        data = request.read().decode(encoding)
        return json.loads(data)
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Plugin('smarthome-dummy')
    myplugin.run()


#######################################################################
# UTIL FUNCTIONS
#######################################################################

def get_interface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])


def get_lan_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127.") and os.name != "nt":
            interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "wifi0", "ath0", "ath1", "ppp0"]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break
                except IOError:
                    pass
        return ip
    except Exception as err:
        return get_lan_ip_fallback()

def get_lan_ip_fallback():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.connect(('<broadcast>', 0))
        return s.getsockname()[0]
    except Exception as err:
        logger.critical(err)
        return None

