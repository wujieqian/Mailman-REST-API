#!/usr/bin/python

import sys
import os
import re
import subprocess
import json
import yaml

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


DEBUG = True

app = Flask(__name__)
api = Api(app)

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
    print byaddrs
    subs = byaddrs.items()
    subs.sort()

    print 'subs %s' % subs
    for addr, id in subs:
        print addr, id

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
        print 'login fail, password error'
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
    if DEBUG is True:
        #bypass this check.
        return True

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
    print subs
    for i in subs:
        addr = i[0]
        if verify_qiyi_email_address(addr):
            validMembers.append(i)
        else:
            invalidMembers.append(i)

    if invalidMembers:
        print 'These %s are not qiyi.com' % invalidMembers

    print validMembers
    print 'Approving...'
    
    for addr, ids in validMembers:
        print 'addr id %s, %s' %(addr, ids)
        try:
            id = ids[0]
            mlist.HandleRequest(id, mm_cfg.SUBSCRIBE, None, None, None)

        except Errors.LostHeldMessage:
            # It's OK. Exception just means someone else has already 
            # updated the database 
            continue

    print 'Approval finished'

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
        print e
        return ""

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
        print 'cmd =',cmd
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
        print 'error', 'admindb: No such list "%s": %s\n' % (listname, e)
        raise ValueError('No such list %s' % listname)

    mlist.Lock()
    try:
        mlist_authenticate(mlist, passwd)
        print 'num request pending %s' % mlist.NumRequestsPending()
        subs = do_get_pending_subs(mlist)

    finally:
        mlist.Unlock()
        # only return emails
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
        print 'error', 'admindb: No such list "%s": %s\n' % (listname, e)
        raise ValueError('No such list %s' %(listname))


    mlist.Lock()
    try:
        mlist_authenticate(mlist, passwd)

        print 'num request pending %s' % mlist.NumRequestsPending()
        subs = do_get_pending_subs(mlist)

        # only process specified emails. Or approve all pending emails.
        if memlist and subs:
            subs = [ i for i in subs if i[0] in memlist]

        if subs:
            approvedList = do_approve(mlist, subs)
        else:
            print 'No pending email for approval'

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

        except (KeyError, AssertionError) as e:
            response = jsonify({"message": 'invalid listname/password'})
            response.status_code = 400
            return response

        if pendings:
            msg = '\n'.join(pendings)
        else:
            msg = 'No pending mails.'
        response = jsonify({"message": msg})
        response.status_code = 201
        return response 
        

class ApprovePending(Resource):
    """
    TODO:
    """
    def __init__(self):
        pass

    def post(self):
        """ POST Request URL """
        try:
            list_data = json.dumps(request.get_json(force=True))
            print list_data
            list_data = yaml.safe_load(list_data)
            passwd = list_data['passwd']
            listname = list_data['listname']

            if 'members' in list_data:
                members = list_data['members']
            else:
                members = []
            print passwd, listname,members
            print type(passwd), type(listname), type(members)

            print "[BEGIN]: Approval"
            approved = approve_pending(passwd, listname, members)
            print "[END]: Approval"

        except (KeyError, ValueError) as e:
            response = jsonify({"message": str(e)})
            response.status_code = 400
            return response

        # success
        if approved:
            msg = 'Subscribed: ' + ';'.join(approved)
        else:
            msg = 'None is accepted. Please submit request on Web first.'
        response = jsonify({"message":msg})
        response.status_code = 201
        return response


def post_wrapper(request, func):
    try:
        print request.__str__
        list_data = json.dumps(request.get_json(force=True))
        print list_data
        list_data = yaml.safe_load(list_data)
        passwd = list_data['passwd']
        listname = list_data['listname']

        if 'members' in list_data:
            members = list_data['members']
        else:
            members = []

        mlist = MailList.MailList(listname, lock=0)

        if members:
            mlist_authenticate(mlist, passwd)
            #msg = do_add_members(listname, members)
            msg = func(listname, members)
        else:
            msg = 'No email in request list'

    except (Errors.MMListError, KeyError, ValueError) as e:
        response = jsonify({"message": "list/passwd error"})
        response.status_code = 400
        return response

    # success
    response = jsonify({"message":msg})
    response.status_code = 201
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
        
        
api.add_resource(ShowPending, "/pending")
api.add_resource(ApprovePending, "/approve")
api.add_resource(AddMem, "/add")
api.add_resource(RemoveMem, "/remove")


#
# PART 3. Automation Test
#

def test01_do_add_members():
    mem_list = {'test01@foo.com',
                'test02@foo.com'
                }
    try:
        do_add_members('dummy', mem_list)
        
    finally:
        #cleanup test
        do_remove_members('dummy', mem_list)

#
# PART 4. Misc
#

def main():
    app.run(host='0.0.0.0', debug=DEBUG)


if __name__ == '__main__':
    main()
