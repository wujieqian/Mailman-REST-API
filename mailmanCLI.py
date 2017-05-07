#!/usr/bin/python
import sys
import re
import requests
import getopt
import getpass
import json
import yaml
from requests import get
from requests import post

import pdb

SERVER='127.0.0.1'
PORT=5000
#PASSWD = None

DEBUG = False
PASSWD = 'l1admin'


ACTIONS = ('add', 'remove', 'show-pending', 'approve')


def check_mail_address(mail):
    if DEBUG:
        return True
    return True if re.match("^.+\\@qiyi.com", mail) else False


def show_usage():

    _str =  '\t'+ '\n\t'.join(ACTIONS)
    usage = 'mailmanCLI <action> [options] [mails,] listname\n' + \
            'Here are valid actions:\n' + _str + '\n'

    optionArgs ="""
optional arguments:
    -h show this help message and exit
    -f file 
        A file containing addresses of the members to be added, one address
        per line.
"""

    print usage
    print optionArgs

def parseArguments(args):
    class ArgsException(Exception):
        pass

    try:
        action = args[0]
        if action not in ACTIONS:
            raise ArgsException('{0} is not a valid action'.format(action))

        options, args = getopt.getopt(args[1:], 'hf:')
        mailFile = None
        printUsage = False
        pdb.set_trace()
        for o, val in options:
            if o in ('-f'):
                mailFile = val
            elif o in ('-h'):
                printUsage = True
            else:
                print 'Unknow option {0}'.format(o)
                show_usage()

        if printUsage:
             show_usage()
             exit(0)
        if not args:
            raise ArgsException("No listname.")
        
        mails = args[1:-1]
        listname = args[-1]
        mails = [m for m in mails if check_mail_address(m)]

    except ArgsException as e:
        print str(e)
        show_usage()
        exit(1)

    return action, mailFile, mails, listname

def get_full_mails(mailFile):
    try:

        with open(mailFile) as f:
            for mail in f:
                if check_mail_address(mail):
                    mails.append(mail)
                else:
                    print '{0} is not a valid qiyi.com address'.format(mail)

    except Exception as e:
        print str(e)
        exit(1)
    return mails


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
        except requests.exceptions.ConnectionError as e:
            print str(e)
        except Exception as e:
            print str(e)
    
    def _wrap_request(self):
        self.headers={
            'Content-Type':'application/json'
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


def main(args):
    global PASSWD
    action, mailFile, mails, listname = parseArguments(sys.argv[1:])

    mails = list(set(mails))
    pdb.set_trace()
    if mailFile:
        mailsFromFile = get_full_mails(mailFile)
        if mailsFromFile and mails:
            mails = list(set(mailsFromFile) & set(mails))
        
    if PASSWD is None:
        PASSWD = getpass.getpass("Please input your admin/moderator password:")

    sendRequest(action, PASSWD, listname, mails)


def test():
    sendRequest('pending', 'l1admin', 'dummy')
    sendRequest('add', 'l1admin', 'dummy', ['add_a_test@foo.com','def@foo.com'])
    sendRequest('remove', 'l1admin', 'dummy', ['add_a_test@foo.com','def@foo.com'])


if __name__ == '__main__':
    main(sys.argv[1:])
