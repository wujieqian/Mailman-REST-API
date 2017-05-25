import sys
sys.path.append('mailmancli/')
sys.path.append('mailmanrest/')
import mailmancli as M

"""
This test program is driven by pytest tool. 
    pip install -U pytest
Please manually subscribe a mail named 'foo_test@foo.com' before test.
After testing, this mail will be removed.
"""

def test_001_add_mails_in_args():
    add_args = ['add', 'add_one@test.com', 'add_two@test.com', 'dummy']
    remove_args = ['remove', 'add_one@test.com', 'add_two@test.com', 'dummy']

    #init env
    M.send_request(remove_args)

    #do test
    msg = M.send_request(add_args).message
    assert('Subscribed' in msg)

    #clean up
    msg = M.send_request(remove_args).message
    assert('Remove Successfully' in msg)

    msg = M.send_request(remove_args).message
    assert('No such member' in msg)

def test_002_add_mails_in_file():
    mails = ['add_one@test.com', 'add_two@test.com']
    mail_file = '/tmp/mailman.test.tmp'

    add_args = ['add', '-f', mail_file, 'dummy']
    remove_args = ['remove', 'add_one@test.com', 'add_two@test.com', 'dummy']

    with open(mail_file, 'w') as f:
        for m in mails:
            f.write(m+'\n')

    M.send_request(remove_args)
    msg = M.send_request(add_args).message
    for i in mails:
        assert('Subscribed: {0}'.format(i) in msg)

    M.send_request(remove_args)


def test_003_add_mails_from_both():
    mails = ['add_one@test.com', 'add_two@test.com']
    mail_file = '/tmp/mailman.test.tmp'

    add_args = ['add', '-f', mail_file, 'add_three@test.com', 'dummy']
    remove_args = ['remove', 'add_one@test.com', 'add_two@test.com', 'dummy']

    with open(mail_file, 'w') as f:
        for m in mails:
            f.write(m+'\n')
    
    M.send_request(remove_args)
    msg = M.send_request(add_args).message
    mails.append('add_three@test.com')
    for i in mails:
        assert('Subscribed: {0}'.format(i) in msg)

    M.send_request(['remove', 'add_three@test.com', 'dummy'])
