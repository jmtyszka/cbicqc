#!/bin/bash
#
# Master QC analysis script
#
# USAGE: cbicqc_all.sh <Overwrite [Y|N]>
#
# Query and retrieve new QC studies for all scanners from the local OsiriX database
# Use dcmtk command line functions to generate list of new QC data and 
# copy DICOM files into QC directory tree ready for analysis.
#
# AUTHOR : Mike Tyszka, Ph.D.
# PLACE  : Caltech Brain Imaging Center
# DATES  : 10/10/2011 JMT From scratch
#          10/16/2012 JMT Add local OsiriX Q&R to get QC study data
#          10/19/2012 JMT Add optional overwrite argument
#          02/19/2014 JMT Generalize to multiple scanners
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
# Copyright 2011-2014 California Institute of Technology.

# QC data/website directory
if [ -z "${CBICQC_DATA}" ]; then
  echo "Please define CBICQC_DATA undefined - exiting"
  exit
fi

if [ $# -lt 1 ]; then
  overwrite="N"
else
  overwrite=$1
fi

echo "CBIC QC Analysis"
echo "----------------"
echo "QC Data Directory : ${CBICQC_DATA}"

# Call cbicqc_scanner.sh for each scanner

# Siemens TIM32
cbicqc_scanner.sh TIM_32 "-k 0008,1000=35077 -k 0010,0010=qc -k 0010,0020=qc" ${overwrite}

# Siemens TIM12
# cbicqc_scanner.sh TIM_12 "-k 0008,1000=35408 -k 0010,0010=qc -k 0010,0020=qc" ${overwrite}

# 4.7T Bruker
# cbicqc_scanner.sh BRK_47 "-k 0008,0070=Bruker -k 0010,0010=QC" ${overwrite}

# Create home page for QC reports linking each scanner's report
# Final report HTML file is in $qc_data/qc_report.html

cbicqc_report_all.py ${CBICQC_DATA}
