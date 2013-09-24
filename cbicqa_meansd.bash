#!/bin/bash
#
# Calculate column mean and sd in a text file of floats
#
# AUTHOR : Mike Tyszka, Ph.D.
# DATES  : 10/25/2012 JMT From scratch
#
# Copyright 2012 California Institute of Technology
# All rights reserved

# Arguments
filename=$1
column=$2

awk -v c=$column '
  BEGIN { sum = 0; sum2 = 0 }
  { sum += $c; sum2 += $c*$c }
  END { printf "%0.5f %0.5f", sum/NR,sqrt( (sum2 - sum*sum/NR) / NR ) }
' ${filename}