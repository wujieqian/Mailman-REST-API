#!/bin/bash
# 
# The test is driven by Pytest. Please install it before test.
#   pip install -U pytest
#

# 
# env MUST be set before testing
#
export MAILMAN_PASSWD='l1admin'

#
# env vars that can keep default values.
#
export PYTHONPATH='/usr/lib/mailman/'}
export MAILMAN_TEST='TRUE'
export TEST_LIST_NAME='dummy'
export TEST_LIST_ADMIN='foo@test.com'

CONFIG=/tmp/mailman.${TEST_LIST_NAME}.conf

function info {
	echo 'INFO:' $@
}

function fatal {
	echo 'FATAL:' $@
	exit 1
}
function warn {
    echo 'WARN:' $@
}

mailman=/usr/lib/mailman/bin

#
# Init TEST env
#
# Check if list exists. If not, create it.
${mailman}/list_lists | (grep -i $TEST_LIST_NAME >/dev/null 2>&1)
ret=$?
if [ $ret = 0 ] ; then
    info "mail list ${TEST_LIST_NAME} exists"
else
    ${mailman}/newlist -q -a $TEST_LIST_NAME $TEST_LIST_ADMIN $MAILMAN_PASSWD \
        >/dev/null 2>&1
    ret=$?
    if [ $ret = 1 ]; then
        fatal "create new list $TEST_LIST_NAME fail"
    fi
fi

# Set list property. subscribe_policy = 'Require approval'
echo 'subscribe_policy = 2' > $CONFIG
${mailman}/config_list -i $CONFIG $TEST_LIST_NAME

# Check if mailmanrest is running.
if ! pgrep -f mailmanrest.py >/dev/null; then
    fatal 'mailmanrest.py is not running'
fi

#
# Run TEST
#
py.test test/mailmanTest.py

#
# Cleanup TEST env
#
#${mailman}/rmlist $TEST_LIST_NAME

