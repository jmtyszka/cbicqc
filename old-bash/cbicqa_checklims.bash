#!/bin/bash
#
# Return an HTML table row for a given value and acceptable limits with colored check string
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 10/16/2012 JMT From scratch
#
# Copyright 2012 California Institute of Technology
# All rights reserved

var_name=$1
var_value=$2
var_lower=$3
var_upper=$4

# Use awk to generate correct check string
check_str=`echo $2 $3 $4 | awk '{ if ($1 < $2 || $1 > $3) { print "<p style=""color:red"">Fail</p>" } else { print "<p style=""color:green"">Pass</p>" } }'`

# Construct HTML code string to return
echo "<tr><td><b>${var_name}</b><td>${var_value}<td>${var_lower}<td>${var_upper}<td>${check_str}</tr>"
