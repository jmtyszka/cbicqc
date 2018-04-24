#!/bin/bash
#
# Calculate column mean and sd in a text file of floats
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 10/25/2012 JMT From scratch
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

# Arguments
filename=$1
column=$2

awk -v c=$column '
  BEGIN { sum = 0; sum2 = 0 }
  { sum += $c; sum2 += $c*$c }
  END { printf "%0.5f %0.5f", sum/NR,sqrt( (sum2 - sum*sum/NR) / NR ) }
' ${filename}
