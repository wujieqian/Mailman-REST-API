#!/usr/bin/python

import sys
import os
import re
import subprocess
import json
import yaml
import logging
import logging.config
from logging.handlers import RotatingFileHandler
import pdb

#Mailman2.1 python lib
sys.path.append('/usr/lib/mailman')

from Mailman import mm_cfg
from Mailman import MailList
from Mailman import Errors

from flask import Flask
from flask import request
from flask import jsonify
from flask_restful import Api
from flask_restful import reqparse
from flask_restful import Resource


app = Flask(__name__)
api = Api(app)
logger = app.logger

_TEST = 'TRUE'

#
# PART 1. Internal Functions of Processing Mailman Database.
#

def do_get_pending_subs(mlist):
    """
    Description:
        return pending subscribtion requests.
        Note this func needs Mailman internal instacnces as Args.
    Args:
        mlist: mlist instance
    Return:
        subs: subscribtion list, like:
            [('abcd@qiyi.com', [5])] 
    """
    pendingsubs = mlist.GetSubscriptionIds()

    if not pendingsubs:
        return None 

    byaddrs = {}
    for id in pendingsubs:
        addr = mlist.GetRecord(id)[1]
        byaddrs.setdefault(addr, []).append(id)
    logger.debug(byaddrs)
    subs = byaddrs.items()
    subs.sort()

    logger.debug('subscriptions: %s' % subs)
    for addr, id in subs:
        logger.debug('addr:{0}, id:{1}'.format(addr, id))

    return subs

def mlist_authenticate(mlist, passwd):
    """
    Description: Authenticate mlist. It's strongly recommended
    that do mlist.lock() before authentication.
    """
    if not mlist.WebAuthenticate((mm_cfg.AuthListAdmin,
                                  mm_cfg.AuthListModerator,
                                  mm_cfg.AuthSiteAdmin),
                                  passwd):
        logger.warning('login fail, password error')
        raise ValueError('Admin/Moderator password error')

def verify_qiyi_email_address(addr):
    """
    Description:
        check if email address is @qiyi.com
    Args:
        email address
    Return:
        True: addr is @qiyi.
        False: addr is not @qiyi. 
    """
    pdb.set_trace()
    if _TEST == 'TRUE':
        return True if re.match("^.+\\@test.com", addr) else False
    return True if re.match("^.+\\@qiyi.com", addr) else False
    

def do_approve(mlist, subs):
    """
    Description: This function is used to accept subscribtion
        requests. All requests are submitted on Mailman Web and pending
        on Admin/Moderator approval. Only qiyi.com emails can be accepted.
        Note this func uses Mailman internal instacnces as Args.

    Args:
        mlist: Mailman internal MailList instance.
        subs: subscribtion list, like:
            [('abcd@qiyi.com', [5])] 
    """
    validMembers= []
    invalidMembers = []
    for i in subs:
        addr = i[0]
        if verify_qiyi_email_address(addr):
            validMembers.append(i)
        else:
            invalidMembers.append(i)

    if invalidMembers:
        logger.info('These %s are not qiyi.com' % invalidMembers)
        

    logger.info('Approving members:{0}'.format(validMembers))
    
    for addr, ids in validMembers:
        logger.debug('addr id %s, %s' %(addr, ids))
        try:
            id = ids[0]
            mlist.HandleRequest(id, mm_cfg.SUBSCRIBE, None, None, None)

        except Errors.LostHeldMessage:
            # It's OK. Exception just means someone else has already 
            # updated the database 
            continue

    logger.info('Approval finished')

    return [i[0] for i in validMembers]


def do_add_members(listname, memberList):
    """
    Description:
        Call CMD mailman/bin/add_member to add a list of members.
        Note this function uses normal list as Args.
    Args:
        memberList: email address list to be added.
        listname: mail list
    """
    memstr = '\n'.join(memberList)
    cmd = ['add_members', '-r', '-']
    cmd.append(listname)

    try:
        child = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stdin=subprocess.PIPE)
        msg = child.communicate(memstr)
        ret = child.wait()

        return msg[0]
    except IOError, e:
        logger.warning(str(e))
        return "fatal issue when adding members."

def do_remove_members(listname, memberList):
    """
    Description:
        Call CMD mailman/bin/remove_member to add a list of members.
    Args:
        memberList: email address list to be removed.
        listname: mail list
    """
    memstr = '\n'.join(memberList)
    cmd = ['remove_members', '-f', '-']
    cmd.append(listname)

    try:
        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        msg = child.communicate(memstr)

        # don't care ret val.
        child.wait()

        if not msg[0]:
            return "Remove Successfully"
        else:
            return msg[0]
    except IOError, e:
        print e
        return "Internal Error"

def show_pending(passwd, listname):
    try:
        mlist = MailList.MailList(listname, lock=0)
    except Errors.MMListError, e:
        logger.warning('error', 'admindb: No such list {0}": {1}\n'.formati(listname, e))
        raise ValueError('No such list %s' % listname)

    mlist.Lock()
    subs = []
    try:
        mlist_authenticate(mlist, passwd)
        subs = do_get_pending_subs(mlist)
    finally:
        mlist.Unlock()
    if subs:
        return [i[0] for i in subs]
    else:
        return None

        
def approve_pending(passwd, listname, memlist=None):
    """
    Description: if memlist is None, add all pending members, or
        only add memlist.
    """
    approvedList = []

    try:
        mlist = MailList.MailList(listname, lock=0)
    except Errors.MMListError, e:
        logger.warning('error', 'admindb: No such list "%s": %s\n' % (listname, e))
        raise ValueError('No such list %s' %(listname))

    mlist.Lock()
    try:
        mlist_authenticate(mlist, passwd)

        logger.debug('num request pending %s' % mlist.NumRequestsPending())
        subs = do_get_pending_subs(mlist)

        # only process specified emails. Or approve all pending emails.
        if memlist and subs:
            subs = [ i for i in subs if i[0] in memlist]

        if subs:
            approvedList = do_approve(mlist, subs)
        else:
            logger.debug('No acceptable member.')

        # apply all changes.
        mlist.Save()
    finally:
        mlist.Unlock()
    return approvedList

#
# PART 2. External REST API.
#

class ShowPending(Resource):

    def __init__(self):

        self.keys = [ 'listname',
                      'passwd'
                    ]
        self.parser = reqparse.RequestParser()
        for k in self.keys:
            self.parser.add_argument(k, type=str)

    def get(self):
        """ GET Request URL"""
        args = self.parser.parse_args()
        try:
            passwd = args['passwd']
            listname = args['listname']
            assert(passwd)
            assert(listname)
            pendings = show_pending(passwd, listname)

        except KeyError as e:
            response = jsonify({"message": 'Please set listname and passwd in request'})
            response.status_code = 400
            return response
        except ValueError as e:
            response = jsonify({"message": str(e)})
            response.status_code = 400
            return response

        if pendings:
            msg = '\n'.join(pendings)
        else:
            msg = 'No pending mails.'
        response = jsonify({"message": msg})
        response.status_code = 200
        return response 
        

class ApprovePending(Resource):
    def __init__(self):
        pass

    def post(self):
        """ POST Request URL """
        try:
            list_data = json.dumps(request.get_json(force=True))
            list_data = yaml.safe_load(list_data)
            passwd = list_data['passwd']
            listname = list_data['listname']

            if 'members' in list_data:
                members = list_data['members']
            else:
                members = []

            logger.debug("[start] approval")
            approved = approve_pending(passwd, listname, members)
            logger.debug("[end] approval")

        except (KeyError, ValueError) as e:
            response = jsonify({"message": str(e)})
            response.status_code = 400
            return response

        # success
        if approved:
            msg = 'Subscribed: ' + ';'.join(approved)
        else:
            msg = 'Mails in request are not pending/valid members. Please submit request on Website first.'
        response = jsonify({"message":msg})
        response.status_code = 200
        return response


def post_wrapper(request, func):
    try:
        list_data = json.dumps(request.get_json(force=True))
        list_data = yaml.safe_load(list_data)

        logger.info(list_data)
        passwd = list_data['passwd']
        listname = list_data['listname']

        if 'members' in list_data:
            members = list_data['members']
        else:
            members = []

        mlist = MailList.MailList(listname, lock=0)

        if members:
            mlist_authenticate(mlist, passwd)
            msg = func(listname, members)
        else:
            msg = 'No email in request list'

    except (Errors.MMListError, KeyError, ValueError) as e:
        logger.warning(str(e))
        response = jsonify({"message": "list/passwd error"})
        response.status_code = 400
        return response
    except Exception as e:
        logger.error(str(e))
        response = jsonify({"message": "Fatal internal error"})
        response.status_code = 500
        return response

    # success
    response = jsonify({"message":msg})
    response.status_code = 200
    return response


class AddMem(Resource):
    def __init__(self):
        pass

    def post(self):
        return post_wrapper(request, do_add_members)


class RemoveMem(Resource):
    def __init__(self):
        pass

    def post(self):
        return post_wrapper(request, do_remove_members)
        
        
api.add_resource(ShowPending, "/api/pending")
api.add_resource(ApprovePending, "/api/approve")
api.add_resource(AddMem, "/api/add")
api.add_resource(RemoveMem, "/api/remove")

def set_logger(logPath):
    formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                  "%(levelname)s - %(message)s")

    file_handler = RotatingFileHandler(logPath, 
                                        maxBytes=10000, 
                                        backupCount=1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()  
    console_handler.setLevel(logging.DEBUG)  
    console_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler) 
    app.logger.addHandler(console_handler) 
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.addHandler(console_handler)


def main(logPath):
    set_logger(logPath)
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main(sys.argv[1])
