#!/bin/bash

#curl http://localhost:5000/approve -H "Content-Type: application/json" -i -d '{"passwd":"l1admin", "list":"dummy", "members":["abc@foo.com", "def@foo.com"]}' -X PUT
#curl http://localhost:5000/approve -H "Content-Type: application/json" -i -d '{"passwd":"l1admin", "list":"dummy", "members":["iii@foo.com", "def@foo.com"]}' -X POST
#curl http://localhost:5000/approve -H "Content-Type: application/json" -i -d '{"passwd":"l1admin", "list":"dummy", "members":["add_a_test@foo.com", "def@foo.com"]}' -X POST

#curl http://localhost:5000/approve -H "Content-Type: application/json" -i -d '{"passwd":"l1admin", "list":"dummy"}' -X POST

#curl http://localhost:5000/pending  -i -d "passwd=l1admin" -d "listname=dummy" -X GET


curl http://localhost:5000/add -H "Content-Type: application/json" -i -d '{"passwd":"l1admin", "list":"dummy", "members":["add_a_test_2@foo.com", "def@foo.com"]}' -X POST
#curl http://localhost:5000/remove -H "Content-Type: application/json" -i -d '{"passwd":"l1admin", "list":"dummy", "members":["add_a_test_2@foo.com", "def@foo.com"]}' -X POST

#wrong passwd
curl http://localhost:5000/add -H "Content-Type: application/json" -i -d '{"passwd":"l1adminabc", "list":"dummy", "members":["add_a_test_2@foo.com", "def@foo.com"]}' -X POST
