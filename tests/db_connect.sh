#!/usr/bin/env bash

# $1: database uri
# $2: database name
# $3: username
# $4: password

mysql -u $3 -p$4 -h $1 $2

