#!/bin/bash
#
# This script will rm all Mailman locks file. 
# If MailmanREST server hang, it most like lock issue happened.
# Please run this script carefully.
#

ls -al /var/lib/mailman/locks/
sudo rm -rf /var/lib/mailman/locks/*lock*
