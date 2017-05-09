#!/usr/bin/python
import sys
import os
import re
import requests
import getopt
import getpass
import json
import yaml
from requests import get
from requests import post

import pdb

SERVER = os.getenv('MAILMAN_SERVER') or '127.0.0.1'
PORT = 5000
PASSWD = os.getenv('MAILMAN_PASSWD')

ACTIONS = ('add', 'remove', 'show-pending', 'approve')
_TEST = os.getenv('MAILMAN_TEST') or 'FALSE'

def check_mail_address(mail):
    if _TEST == 'TRUE':
        return True if re.match("^.+\\@test.com", mail) else False
    return True if re.match("^.+\\@qiyi.com", mail) else False


def show_usage():
    usage = """
mailmanCLI <action> [options] [mails,] listname
    Here are valid actions:
        add: add *@qiyi.com members in [mails,] and [-f file]
        remove: remove *@qiyi.com members in [mails,] and [-f file]
        show-pending: list members waiting for approval.
        approve:  if [mails] or [-f file] are null, all pending members will be approved.
"""

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
        if not args:
            raise ArgsException()
        action = args[0]
        if action!='-h' and action not in ACTIONS:
            raise ArgsException('A action must be specified.')

        if args[0][0] != '-':
            args = args[1:]

        options, args = getopt.getopt(args, 'hf:')
        mailFile = None
        printUsage = False
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
        
        mails = args[:-1]
        listname = args[-1]
        #mails = [m for m in mails if check_mail_address(m)]
        valid_mails = []

        for m in mails:
            if check_mail_address(m):
                valid_mails.append(m)
            else:
                print '{0} is not a valid qiyi.com address'.format(m)

    except Exception as e:
        print str(e)
        show_usage()
        exit(1)

    return action, mailFile, valid_mails, listname

def get_file_mails(mailFile):
    try:
        mails = []
        with open(mailFile) as f:
            for mail in f:
                mail = mail.strip()
                if not mail:
                    continue
                if check_mail_address(mail):
                    mails.append(mail)
                else:
                    print '{0} is not a valid qiyi.com address'.format(mail)

    except Exception as e:
        print str(e)
        exit(1)
    return mails


class sendRequest(object):
    actions_method = {'add':post, 'remove':post, 'approve':post, 'show-pending':get}
    actions_url = {'add':'add', 'remove':'remove', 'approve':'approve', 'show-pending':'pending'}
    baseURL="http://{0}:{1}/api/".format(SERVER, str(PORT))

    def __init__(self, action, passwd, listname, members=None):
        self.passwd = passwd
        self.listname = listname
        self.members = members
        self.response = None
        self.message = None
        try:
            method = sendRequest.actions_method[action]
            self._wrap_request()
            self._send(method, sendRequest.baseURL + 
                               sendRequest.actions_url[action])
            self._get_message()
        except requests.exceptions.ConnectionError as e:
            print str(e)
        except Exception as e:
            print str(e)

    def __str__(self):
        return self.message or ''
    
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
        self.message = data['message']
        print data['message']
        print self.response.status_code


def send_request(args):
    """
    This function does 3 tasks.
        1. parse arguments.
        2. combine member lists from [mails,] and [-f file].
        3. kick off request to Mailman server.
    """
    global PASSWD
    action, mailFile, mails, listname = parseArguments(args)

    mails = list(set(mails))
    if mailFile:
        mailsFromFile = get_file_mails(mailFile)
        if mailsFromFile:
            mails = list(set(mailsFromFile) | set(mails))
        
    if PASSWD is None:
        PASSWD = getpass.getpass("Please input your admin/moderator password:")

    if action in ('add', 'remove', 'approve') and not mails:
        print 'No mail found'
        return
    
    return sendRequest(action, PASSWD, listname, mails)


if __name__ == '__main__':
    send_request(sys.argv[1:])
