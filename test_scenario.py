#!/usr/bin/python
import requests
import getopt
import json
import yaml
from requests import get
from requests import post

import pdb

SERVER='127.0.0.1'
PORT=5000

class sendRequest(object):
    actions = {'add':post, 'remove':post, 'approve':post, 'pending':get}
    baseURL="http://{0}:{1}/".format(SERVER, str(PORT))

    def __init__(self, action, passwd, listname, members=None):
        self.passwd = passwd
        self.listname = listname
        self.members = members
        self.response = None

        try:
            method = sendRequest.actions[action]
            self._wrap_request()
            self._send(method, sendRequest.baseURL+action)
            self._get_message()
        except KeyError as e:
            print str(e)
        except requests.exceptions.ConnectionError as e:
            print str(e)
    
    def _wrap_request(self):
        self.headers={
            'Content-Type':'application/json'
            #'Accept': 'application/json',
            } 
    
        self.data={
            'passwd' : self.passwd,
            'listname' : self.listname,
            }
    
        if self.members:
            self.data['members'] = self.members
        
    def _send(self, method, url):
        if method is post:
            self.data = json.dumps(self.data)
        if method is get:
            self.response = method(url, self.data)
        else:
            self.response = method(url, self.data, self.headers)

    def _get_message(self):
        raw_data = json.dumps(self.response.json())
        data = yaml.safe_load(raw_data)
        print data['message']
        print self.response.status_code


def main():
    #sendRequest('pending', 'l1admin', 'dummy')
    sendRequest('add', 'l1admin', 'dummy', ['add_a_test@foo.com','def@foo.com'])


if __name__ == '__main__':
    main()
