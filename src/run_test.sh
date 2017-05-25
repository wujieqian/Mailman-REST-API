#!/bin/bash
#
# The test is driven by Pytest. Please install it before test.
#   pip install -U pytest
#

#
# env vars used in test.
#
export PYTHONPATH='/usr/lib/mailman/'}
export MAILMAN_TEST='TRUE'

# please set Mailman admin password
export MAILMAN_PASSWD='l1admin'

py.test test/mailmanTest.py
