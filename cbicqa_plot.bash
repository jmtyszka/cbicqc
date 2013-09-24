#!/bin/bash
#
# Create plot image of column in qa.dat
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#
# Copyright 2011 California Institute of Technology
# All rights reserved.

if [ $# -lt 3 ]; then
  echo "-----------------"
  echo "SYNTAX : cbicqa_pot.bash <Data File> <Column> <Output> <YMin> <YMax>"
  exit
fi

data=$1
col=$2
out=$3
ymin=$4
ymax=$5

# Plot graph as PBM image
gnuplot << ENDPLOT
set output '${out}.pbm'
set term pbm size 800,200 color
set xdata time
set yrange [${ymin}:${ymax}]
set timefmt '%Y-%m-%d'       # YYYY-MM-DD formate dates
set format y '%10.3f'
set datafile separator ','   # CSV File
# Plot values from CSV file, starting at second line (skip header row)
plot '${data}' using 2:${col} every ::2 notitle with points lt 3 pt 6 ps 3
ENDPLOT

# Convert to PNG
convert ${out}.pbm ${out}.png

# Remove PBM image
rm -rf ${out}.pbm
