#!/bin/bash
#
# Return an HTML table row for a given value and acceptable limits with colored check string
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 10/16/2012 JMT From scratch
#
# This file is part of CBICQC.
#
#    CBICQC is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    CBICQC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#   along with CBICQC.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2012-2013 California Institute of Technology.

var_name=$1
var_value=$2
var_lower=$3
var_upper=$4

# Use awk to generate correct check string
check_str=`echo $2 $3 $4 | awk '{ if ($1 < $2 || $1 > $3) { print "<p style=""color:red"">Fail</p>" } else { print "<p style=""color:green"">Pass</p>" } }'`

# Construct HTML code string to return
echo "<tr><td><b>${var_name}</b><td>${var_value}<td>${var_lower}<td>${var_upper}<td>${check_str}</tr>"
