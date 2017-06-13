#!/bin/python
"""
This test program is driven by pytest tool. 
    pip install -U pytest
"""
import sys
import os
sys.path.append('../mailmancli/')
sys.path.append('../mailmanrest/')
import mailmancli as MailCLI
import mailmanrest as MailREST

listname = os.getenv('TEST_LIST_NAME')
passwd = os.getenv('MAILMAN_LIST_PASSWD')
print passwd

def test_001_add_mails_in_args():
    add_args = ['add', 'first@test.com', 'second@test.com', listname]
    remove_args = ['remove', 'first@test.com', 'second@test.com', listname]

    #init env
    MailCLI.send_request(remove_args)

    #do test
    msg = MailCLI.send_request(add_args).message
    assert('Subscribed' in msg)

    #clean up
    msg = MailCLI.send_request(remove_args).message
    assert('Remove Successfully' in msg)
    msg = MailCLI.send_request(remove_args).message
    assert('No such member' in msg)


def test_002_add_mails_in_file():
    mails = ['first@test.com', 'second@test.com']
    mail_file = '/tmp/mailman.test.tmp'

    add_args = ['add', '-f', mail_file, listname]
    remove_args = ['remove', 'first@test.com', 'second@test.com', listname]

    with open(mail_file, 'w') as f:
        for m in mails:
            f.write(m+'\n')

    MailCLI.send_request(remove_args)
    msg = MailCLI.send_request(add_args).message
    for i in mails:
        assert('Subscribed: {0}'.format(i) in msg)

    MailCLI.send_request(remove_args)


def test_003_add_mails_from_both():
    mails = ['first@test.com', 'second@test.com']
    mail_file = '/tmp/mailman.test.tmp'

    add_args = ['add', '-f', mail_file, 'third@test.com', listname]
    remove_args = ['remove', 'first@test.com', 'second@test.com', listname]

    with open(mail_file, 'w') as f:
        for m in mails:
            f.write(m+'\n')
    
    MailCLI.send_request(remove_args)
    msg = MailCLI.send_request(add_args).message
    mails.append('third@test.com')
    for i in mails:
        assert('Subscribed: {0}'.format(i) in msg)

    MailCLI.send_request(['remove'] +  mails + [listname])


def test_004_show_and_approve_pending():
    mail = 'apply_for_approval@test.com'
    show_pending_args = ['show-pending', listname]
    approve_pending_args = ['approve', mail, listname]
    
    # clean list
    MailCLI.send_request(['remove', mail, listname])

    # use mailmanrest internal function to subscribe a mail.
    MailREST.subscribe(passwd, listname, mail)

    msg = MailCLI.send_request(show_pending_args).message
    assert(mail in msg)
    
    msg = MailCLI.send_request(approve_pending_args).message
    assert('Subscribed' in msg)

    msg = MailCLI.send_request(show_pending_args).message
    assert(mail not in msg)

