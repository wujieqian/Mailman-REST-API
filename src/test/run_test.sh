#!/bin/bash
# 
# The test is driven by Pytest. Please install it before test.
# By default, this test run mailmanrest.py automaticlly.
# You can also have a running mailmanrest.py, then run this script
# with option '-s':
#     sudo ./run_test -s

#
# env vars that can keep default values.
#
MAILMAN_HOME=/var/lib/mailman
MAILMAN_REST_HOME=$(readlink -f $0|xargs dirname|xargs dirname)
export MAILMAN_TEST='TRUE'
export MAILMAN_SERVER='127.0.0.1'
export TEST_LIST_NAME='test_mailman'
export TEST_LIST_ADMIN='foo@test.com'
export MAILMAN_LIST_PASSWD='test'

# tmp file for set list properties.
CONFIG=/tmp/mailman.${TEST_LIST_NAME}.conf

# mailman utils
UTILS=${MAILMAN_HOME}/bin

#run mailmanrest outside the script
STANDALONE=false

########################################
#
#  PART 1. util
#
########################################
function info {
    echo 'INFO:' $@
}

function fatal {
    echo 'FATAL:' $@
    test_cleanup
    exit 1
}
function warn {
    echo 'WARN:' $@
}


########################################
#
#  PART 2. check funtions
#
########################################

#
# Check if list exists. If not, create it.
#
function check_list {
    ${UTILS}/list_lists | (grep -i $TEST_LIST_NAME >/dev/null 2>&1)
    ret=$?
    if [[ $ret = 0 ]] ; then
        info "mail list ${TEST_LIST_NAME} exists"
    else
        ${UTILS}/newlist -q -a $TEST_LIST_NAME $TEST_LIST_ADMIN \
	    $MAILMAN_LIST_PASSWD >/dev/null 2>&1
        ret=$?
        if [ $ret != 0 ]; then
            fatal "create new list $TEST_LIST_NAME fail"
        fi
    fi
    
    # Set list property. subscribe_policy = 'Require approval'
    info "Set $TEST_LIST_NAME subscribe_policy='Require approval'"
    echo 'subscribe_policy = 2' > $CONFIG
    ${UTILS}/config_list -i $CONFIG $TEST_LIST_NAME
}

#
# Check if mailmanrest is running.
#
function check_mailmanrest {
    if [[ $STANDALONE == true ]] && ! pgrep -f mailmanrest >/dev/null; then
	fatal 'mailmanrest is not running'
    fi
    
    # run mailmanrest in test mode
    if [[ -f ${MAILMAN_REST_HOME}/mailmanrest/mailmanrest.py ]]; then 
	pgrep -f mailmanrest >/dev/null && pkill -f mailmanrest
	sudo python ${MAILMAN_REST_HOME}/mailmanrest/mailmanrest.py -t >/dev/null 2>&1 &
    else
	fatal 'can not find mailmanrest.py'
    fi
}


########################################
#
#  PART 3. TEST phases
#
########################################

#
# Init TEST env
#
function test_startup {
    check_list
    check_mailmanrest
}

#
# Cleanup TEST env
#
function test_cleanup {
    ${mailman}/rmlist $TEST_LIST_NAME >/dev/null 2>&1
    [[ $STANDALONE == false ]] && pkill -f mailmanrest
}

#
# Run TEST
#
function run_test {

    while getopts s ARGS
    do
	case $ARGS in
	s)
	    STANDALONE=true
	    ;;	
	*)
	    ;;
	esac
    done

    test_startup
    pytest ${MAILMAN_REST_HOME}/test/mailmantest.py
    test_cleanup
    return 0
}

run_test $@

